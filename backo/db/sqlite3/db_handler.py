# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
DBHandler for Sqlite3
"""

from typing import Any
import copy

import sqlite3

from stricto import SFilter

from ..generic.filter import FilterReport
from ...error import NotFoundError, DBError

from .transformers import IdTransformer, BooleanTransformer, DateTransformer
from ..generic.interface import SelectResponse
from .sql_field import SQlite3FieldDescription
from .table_pragma import SQlite3TablePragma
from .filter import SQlite3Filter
from ..sql.db_handler import DBSQLConnector
from ...sort import Sort
from ...log import log_system

log = log_system.get_or_create_logger("DBSqlite3Connector")


class DBSqlite3Connector(DBSQLConnector):
    """
    DBConnector for sqlite3

    """

    def __init__(
        self,
        db_file: str,
        table_name: str,
        **kwargs,
    ):
        """


        :param db_file: the filename where the DB is stored
        :type db_file: str
        """

        self._db_file = db_file
        self._table_name = table_name

        self.pragmas: dict[str, SQlite3TablePragma] = {}

        self._db_kwargs = kwargs

        super().__init__(f"{db_file}({table_name})", **kwargs)

        self._db_file = db_file
        self._table_name = table_name

        self.register_transformer(IdTransformer())
        self.register_type_transformer(BooleanTransformer())
        self.register_type_transformer(DateTransformer())

        self.filter = SQlite3Filter(self._table_name, self.get_transformer_by_key)

        self.connect()

    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """
        try:
            if not self._db:
                self._db = sqlite3.connect(self._db_file, **self._db_kwargs)
                self._cursor = self._db.cursor()
        except Exception as e:
            raise DBError('Sqlite3 connection error at "{0}"', self._db_file) from e

    def close(self):
        """Close the mongodb connection

        :raise DBError: Raise an error in case of database Error

        """
        try:
            if self._db:
                self._db.close()
                self._db = None
        except Exception as e:
            raise DBError('Sqlite3 close error at "{0}"', self._db_file) from e

    def _drop_table(self, table_name: str, key_path: list[str], model: dict) -> None:
        """
        Drop a table (a main table or a sub table)
        and follow all its fields to check for sub tables.

        :param table_name: the table name
        :type table_name: str
        :param key_path: the table is attach to a key in case of a sub table
        :type key_path: list[str]
        :param model: the model related to the key path
        :type model: dict
        """

        if "sub_scheme" in model:
            for k, v in model["sub_scheme"].items():
                new_key_path = key_path.copy()
                new_key_path.append(k)
                self._drop_table(table_name, key_path + [k], v)
            return

        db_key = "_".join(key_path)

        # A list
        if "sub_type" in model:
            sub_model = model["sub_type"]
            sub_table_name = f"{table_name}_{db_key}"
            self._drop_table(sub_table_name, [], sub_model)
            return

        log.debug(f"DELETE FROM {table_name}")
        self._cursor.execute(f"DELETE FROM {table_name}").fetchall()

        return

    def _fetchall(self, select_str: str, values: tuple[Any] = None) -> list:
        if values:
            log.debug(f"{select_str} with {values}")
            return self._cursor.execute(select_str, values).fetchall()
        return self._cursor.execute(select_str).fetchall()

    def drop(self) -> None:
        """
        Drop the entire collection

        """
        self._drop_table(self._table_name, [], self.model)
        self._db.commit()

    def _set_table_info(self, table_name: str) -> SQlite3TablePragma:
        """
        Fill the SQlite3TablePragma for this table

        :param table_name: the name of the table
        :type table_name: str
        :return: the SQlite3TablePragma found or created
        :rtype: SQlite3TablePragma
        """

        if table_name in self.pragmas:
            tp = self.pragmas[table_name]
        else:
            tp = SQlite3TablePragma(table_name)
            self.pragmas[table_name] = tp

            res = self._cursor.execute(
                f'SELECT name FROM sqlite_master WHERE name=="{table_name}"'
            ).fetchone()
            if res is not None:
                tables = list(res)
                if len(tables) == 1:

                    current_pragmas = self._cursor.execute(
                        f"PRAGMA table_info({table_name});"
                    ).fetchall()

                    for current_pragma in current_pragmas:
                        cp = SQlite3FieldDescription()
                        cp.fill_from_db_pragma(
                            cid=current_pragma[0],
                            db_path=current_pragma[1],
                            sql_type=current_pragma[2],
                            not_null=bool(current_pragma[3]),
                            pk=bool(current_pragma[5]),
                            dflt_value=current_pragma[4],
                            ref_table=None,
                            ref_field=None,
                        )

                        tp.add_db_field(cp)

                    current_foreigns = self._cursor.execute(
                        f"PRAGMA foreign_key_list({table_name});"
                    ).fetchall()

                    for current_foreign in current_foreigns:
                        cp = SQlite3FieldDescription()
                        cp.fill_from_db_pragma(
                            cid=0,
                            db_path=current_foreign[3],
                            sql_type=None,
                            not_null=False,
                            pk=False,
                            dflt_value=None,
                            ref_table=current_foreign[2],
                            ref_field=current_foreign[4],
                        )
                        tp.add_db_field(cp)

            f = SQlite3FieldDescription()
            f.fill_from_backo("id", {"types": ["Int"], "required": False})
            f._pk = True
            tp.add_backo_field(f)

        return tp

    def _reccursive_check_structure(
        self, table_name: str, key_path: list[str], model: dict
    ) -> None:
        """
        Check the structure of the table if compliant to the model

        :param table_name: the table name
        :type table_name: str
        :param key_path: the key path
        :type key_path: list[str]
        :param model: the model of the key path
        :type model: dict
        """

        tp = self._set_table_info(table_name)

        # A Dict
        if "sub_scheme" in model:

            for k, v in model["sub_scheme"].items():
                new_key_path = key_path.copy()
                new_key_path.append(k)
                self._reccursive_check_structure(table_name, new_key_path, v)
            return

        # A List
        if "sub_type" in model:
            sub_table_name = f"{table_name}_{'_'.join(key_path)}"
            self._reccursive_check_structure(sub_table_name, [], model["sub_type"])

            tp_sub = self._set_table_info(sub_table_name)
            f1 = SQlite3FieldDescription()
            f1.fill_from_backo(
                f"{table_name}_id", {"types": ["Int"], "required": False}
            )
            f1._ref_table = table_name
            f1._ref_field = "id"
            tp_sub.add_backo_field(f1)

            return

        # In case of a list of not a Dict,
        if not key_path:
            key_path = ["_"]

        transformer = self.get_transformer_by_key(
            key_path
        )  # , table_name, model["types"])
        store_in_db = True
        db_path = key_path
        db_model = model
        if transformer:
            store_in_db = transformer.must_be_store_in_db()
            db_path = transformer.get_db_path(key_path)
            db_model = transformer.get_db_model(model, key_path)
        if store_in_db:
            f = SQlite3FieldDescription()
            f.fill_from_backo("_".join(db_path), db_model)
            tp.add_backo_field(f)

    def _execute_update_structure(self, s: str) -> None:
        """
        Execute the database modification

        :param s: All command for modification
        :type s: str
        """
        log.debug(s)
        self._cursor.executescript(s)

    def search(self, _id: str) -> dict:  # pylint: disable=unused-argument
        """
        Do a search

        """
        list_of_items = self._search_in_table(self._table_name, "id", int(_id))
        if not list_of_items:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        o = self.load(self._table_name, [], self.model, list_of_items[0])
        return o

    def _search_in_table(self, table_name: str, id_name: str, _id: int) -> list[dict]:
        """
        Do a SELECT into the table for a specific _id name == _id

        :param table_name: the table name
        :type table_name: str
        :param id_name: the name of the field
        :type id_name: str
        :param _id: the id in the equal
        :type _id: int
        :raises NotFoundError: if not found
        :return: datas found as a list of dict
        :rtype: list[dict]
        """

        log.debug(f"SELECT * FROM {table_name} WHERE {id_name} == {_id}")
        list_of_results = self._cursor.execute(
            f"SELECT * FROM {table_name} WHERE {id_name} == ?", (_id,)
        ).fetchall()

        # None or empty
        if not list_of_results:
            return []

        l = []
        for res in list_of_results:
            obj = {}
            for idx, attribute in enumerate(self._cursor.description):
                key_path = attribute[0]
                value = res[idx]
                obj[key_path] = value
            l.append(obj)
        return l

    def _delete_in_table(self, table_name: str, id_name: str, _id: int) -> list[int]:
        """
        Delete in a DB with a WHERE id_name == _id

        :param table_name: the table name
        :type table_name: str
        :param id_name: the name of the field
        :type id_name: str
        :param _id: the value
        :type _id: int
        :raises NotFoundError: if not found
        :return: _descThe list of deleted _ids
        :rtype: list[ int ]
        """
        log.debug(f"DELETE FROM {table_name} WHERE {id_name} == {_id} RETURNING id")
        list_of_results = self._cursor.execute(
            f"DELETE FROM {table_name} WHERE {id_name} == ? RETURNING id", (_id,)
        ).fetchall()

        # None or empty results
        if not list_of_results:
            return []
            # raise NotFoundError(
            #     "{0} == {1} not found in table {2}", id_name, _id, table_name
            # )
        deleted_ids = [res[0] for res in list_of_results]
        return deleted_ids

    def _create_in_table(
        self, table_name: str, keys_values: list[tuple[str, Any]]
    ) -> int:
        """
        Do the creation in the table

        :param table_name: the name of the table
        :type table_name: str
        :param keys_values: list of key, values
        :type keys_values: list[tuple[str, Any]]
        :return: the id created
        :rtype: int
        """
        log.debug(f"Create in table {table_name} {keys_values}")
        r = tuple(map(tuple, zip(*keys_values)))
        t = ("?",) * len(r[0])
        log.debug(
            f"INSERT INTO {table_name} {r[0]} VALUES ({', '.join(t) }) with {r[1]}"
        )
        self._cursor.execute(
            f"INSERT INTO {table_name} {r[0]} VALUES ({', '.join(t) })", r[1]
        )
        created_id = self._cursor.lastrowid
        return created_id

    def _insert_in_table(self, table_name: str, _id: int, keys_values: dict) -> None:
        """
        Do an insert into a table

        :param table_name: the table_name
        :type table_name: str
        :param _id: the _id
        :type _id: int
        :param keys_values: list of key - values
        :type keys_values: dict
        """

        l = []
        v = []
        for key, value in keys_values.items():
            l.append(f"{key} = ?")
            v.append(value)

        v.append(_id)
        log.debug(
            f'UPDATE {table_name} SET {", ".join(l)} WHERE id == ? with {tuple(v)}'
        )
        self._cursor.execute(
            f'UPDATE {table_name} SET {", ".join(l)} WHERE id == ?', tuple(v)
        )

    def save(self, _id: str, o: dict) -> None:
        """save"""
        keys_values = {}
        self._reccursive_save(
            self._table_name, int(_id), [], o, self.model, keys_values
        )
        if keys_values:
            self._insert_in_table(self._table_name, int(_id), keys_values)
        self._db.commit()

    def _reccursive_select(
        self, table_name: str, fields_to_get: str, select_filter: SFilter, model: dict
    ):
        pass

    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter = None,
        projection: list[str] = None,
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: Sort = None,
    ) -> SelectResponse:
        """
        Select from filter in the DB and return a list of dicts, with pagination

        :param select_filter: The filter for selection (depends on DB types)
        :param projection: The list of elements we want for each object
        :type projection: dict
        :param page_size: number of elements per page
        :type page_size: int
        :param num_of_element_to_skip: number of element to skip from beginning
        :type num_of_element_to_skip: int
        :param sort_object: Soon
        :type sort_object: dict
        :raise Error: Raise an error DBError or any db error

        """
        response = SelectResponse(page_size, num_of_element_to_skip)

        (where_conditions, values), filter_report = self.filter.build_db_filter(
            select_filter
        )

        # If the filter will return less elements than the wanted filter, raise an error
        if filter_report == FilterReport.LESS:
            raise DBError(
                f'Sqlite3 filter interpretation cannot be done for filter "{repr(select_filter)}"'
            )

        if filter_report == FilterReport.EXACT:
            response.more_than_filter = False

        sqlite3_sort = self.filter.build_db_sort(sort_object)

        select = f"SELECT * FROM {self._table_name}"
        if where_conditions:
            select += f" WHERE {where_conditions}"

        if sqlite3_sort:
            select += " " + sqlite3_sort
            response.sorted = True

        if page_size:
            values += (page_size,)
            values += (num_of_element_to_skip,)
            select += "LIMIT ? OFFSET ?"

        log.debug(f"{select} {values}")
        # print(f"{select} {values}")
        list_of_items = self._cursor.execute(select, values).fetchall()

        cursor_desc_copy = copy.deepcopy(self._cursor.description)

        # Get the total
        if not page_size:
            response.total = len(list_of_items)

        self._fill_response_with_item(response, list_of_items, cursor_desc_copy)
        return response
