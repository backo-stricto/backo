# pylint: disable=relative-beyond-top-level, no-member
# no-member due to https://github.com/pylint-dev/pylint/issues/10222
"""
DBHandler for Postgres
"""

from typing import Any
import copy

import psycopg

from stricto import SFilter

from ..generic.filter import FilterReport
from ...error import NotFoundError, DBError

from .transformers import IdTransformer
from ..generic.interface import SelectResponse
from .table_pragma import PostgresTablePragma
from .sql_field import PostgresFieldDescription
from .filter import PostgresFilter

from ...sort import Sort
from ...log import log_system

from ..sql.db_handler import DBSQLConnector

log = log_system.get_or_create_logger("DBSpostgresConnector")


class DBPostgresConnector(DBSQLConnector):
    """
    DBConnector for postgress

    """

    def __init__(
        self,
        database_url: str,
        table_name: str,
        **kwargs,
    ):
        """

        :param db_file: the filename where the DB is stored
        :type db_file: str
        """

        self._database_url = database_url
        self._table_name = table_name

        self.pragmas: dict[str, PostgresTablePragma] = {}

        self._db_kwargs = kwargs

        super().__init__(table_name, **kwargs)

        self._database_url = database_url
        self._table_name = table_name

        self.register_transformer(IdTransformer())

        self.filter = PostgresFilter(self._table_name, self.get_transformer_by_key)

        self.connect()

    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """
        try:
            if not self._db:
                self._db = psycopg.connect(self._database_url, **self._db_kwargs)
                self._cursor = self._db.cursor()
        except Exception as e:
            raise DBError(
                'Postgres connection error at "{0}"', self._database_url
            ) from e

    def close(self):
        """Close the Postgres connection

        :raise DBError: Raise an error in case of database Error

        """
        try:
            if self._db:
                self._db.close()
                self._db = None
        except Exception as e:
            raise DBError('Postgres close error at "{0}"', self._database_url) from e

    def drop(self) -> None:
        """
        Drop the entire collection

        """
        log.debug(f"TRUNCATE TABLE {self._table_name} CASCADE;")
        self._cursor.execute(f"TRUNCATE TABLE {self._table_name} CASCADE;")
        self._db.commit()

    def _set_table_info(self, table_name: str) -> PostgresTablePragma:
        """
        Fill the TablePragma for this table

        :param table_name: the name of the table
        :type table_name: str
        :return: the TablePragma found or created
        :rtype: TablePragma
        """

        if table_name in self.pragmas:
            tp = self.pragmas[table_name]
        else:
            tp = PostgresTablePragma(table_name)
            self.pragmas[table_name] = tp

            # Check if the tabke exists
            res = self._cursor.execute(
                """SELECT EXISTS ( SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name=%s);""",
                (table_name,),
            ).fetchone()

            if res is not None and res[0] is True:
                # The table exists, get all information pragma

                res = self._cursor.execute(
                    """
                    SELECT
                        a.attname,
                        UPPER(format_type(a.atttypid, a.atttypmod)),
                        a.attnotnull AS required,
                        COALESCE(pk.is_primary_key, FALSE) AS is_primary_key,
                        COALESCE(fk.is_foreign_key, FALSE) AS is_foreign_key,
                        pg_get_expr(d.adbin, d.adrelid) AS default_value,
                        fk.referenced_table,
                        fk.referenced_column


                    FROM pg_attribute a

                    JOIN pg_class c
                        ON c.oid = a.attrelid

                    JOIN pg_namespace n
                        ON n.oid = c.relnamespace

                    LEFT JOIN pg_attrdef d
                        ON d.adrelid = a.attrelid
                        AND d.adnum = a.attnum

                    LEFT JOIN LATERAL (
                        SELECT TRUE AS is_primary_key
                        FROM pg_constraint con
                        WHERE con.conrelid = c.oid
                          AND con.contype = 'p'
                          AND a.attnum = ANY(con.conkey)
                        LIMIT 1
                    ) pk ON TRUE

                    LEFT JOIN LATERAL (
                        SELECT
                            TRUE AS is_foreign_key,
                            ref.relname AS referenced_table,
                            ref_att.attname AS referenced_column

                        FROM pg_constraint con

                        JOIN pg_class ref
                            ON ref.oid = con.confrelid

                        JOIN LATERAL unnest(con.conkey, con.confkey)
                            AS cols(source_attnum, target_attnum)
                            ON cols.source_attnum = a.attnum

                        JOIN pg_attribute ref_att
                            ON ref_att.attrelid = con.confrelid
                            AND ref_att.attnum = cols.target_attnum

                        WHERE con.conrelid = c.oid
                          AND con.contype = 'f'

                    ) fk ON TRUE

                    WHERE n.nspname = %s
                      AND c.relname = %s
                      AND a.attnum > 0
                      AND NOT a.attisdropped

                    ORDER BY a.attnum;

                """,
                    ("public", table_name),
                ).fetchall()

                for r in res:
                    cp = PostgresFieldDescription()
                    cp.fill_from_pragma(r)
                    tp.add_db_field(cp)

            f = PostgresFieldDescription()
            f.fill_from_backo(
                "id", {"types": ["Id"], "required": True, "default": None}
            )
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
            f1 = PostgresFieldDescription()
            f1.fill_from_backo(
                f"{table_name}_id", {"types": ["Id"], "required": True, "default": None}
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
            f = PostgresFieldDescription()
            f.fill_from_backo("_".join(db_path), db_model)
            tp.add_backo_field(f)

    def _execute_update_structure(self, s: str) -> None:
        """
        Execute the database modification

        :param s: All command for modification
        :type s: str
        """
        log.debug(s)
        self._cursor.execute(s)

    def _search_in_table(self, table_name: str, id_name: str, _id: str) -> list[dict]:
        """
        Do a SELECT into the table for a specific _id name == _id

        :param table_name: the table name
        :type table_name: str
        :param id_name: the name of the field
        :type id_name: str
        :param _id: the id in the equal
        :type _id: UUID
        :raises NotFoundError: if not found
        :return: datas found as a list of dict
        :rtype: list[dict]
        """

        log.debug(f"SELECT * FROM {table_name} WHERE {id_name} = '{_id}'")
        list_of_results = self._cursor.execute(
            f"SELECT * FROM {table_name} WHERE {id_name} = '{_id}'"
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

    def search(self, _id: str) -> dict:  # pylint: disable=unused-argument
        """
        Do a search

        """
        list_of_items = self._search_in_table(self._table_name, "id", _id)
        if not list_of_items:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        o = self.load(self._table_name, [], self.model, list_of_items[0])
        return o

    def _delete_in_table(self, table_name: str, id_name: str, _id: str) -> list[int]:
        """
        Delete in a DB with a WHERE id_name == _id

        :param table_name: the table name
        :type table_name: str
        :param id_name: the name of the field
        :type id_name: str
        :param _id: the value
        :type _id: UUID
        :raises NotFoundError: if not found
        :return: _descThe list of deleted _ids
        :rtype: list[ int ]
        """
        log.debug(f"DELETE FROM {table_name} WHERE {id_name} = '{_id}' RETURNING id")
        list_of_results = self._cursor.execute(
            f"DELETE FROM {table_name} WHERE {id_name} = '{_id}' RETURNING id"
        ).fetchall()

        # None or empty results
        if not list_of_results:
            return []
            # raise NotFoundError(
            #     "{0} == {1} not found in table {2}", id_name, _id, table_name
            # )
        deleted_ids = [res[0] for res in list_of_results]
        return deleted_ids

    def delete_by_id(self, _id):
        """delete"""
        ids = self._delete_in_table(self._table_name, "id", _id)
        if not ids:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        self._reccursive_delete(self._table_name, [], ids, self.model)
        self._db.commit()

    def _create_in_table(
        self, table_name: str, keys_values: list[tuple[str, Any]]
    ) -> str:
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
        log.debug(
            f"INSERT INTO {table_name} ({', '.join(r[0])}) VALUES {r[1]} RETURNING id"
        )
        self._cursor.execute(
            f"INSERT INTO {table_name} ({', '.join(r[0])}) VALUES {r[1]} RETURNING id"
        )
        created_id = self._cursor.fetchone()[0]
        return str(created_id)

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
            l.append(f"{key} = {repr(value)}")
            v.append(value)

        v.append(_id)
        log.debug(f'UPDATE {table_name} SET {", ".join(l)} WHERE id = "{_id}"')
        self._cursor.execute(
            f"UPDATE {table_name} SET {', '.join(l)} WHERE id = '{_id}'"
        )

    def save(self, _id: str, o: dict) -> None:
        """save"""
        keys_values = {}
        self._reccursive_save(self._table_name, _id, [], o, self.model, keys_values)
        if keys_values:
            self._insert_in_table(self._table_name, _id, keys_values)
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

        postgres_sort = self.filter.build_db_sort(sort_object)

        select = f"SELECT * FROM {self._table_name}"
        if where_conditions:
            select += f" WHERE {where_conditions}"

        if postgres_sort:
            select += " " + postgres_sort
            response.sorted = True

        if page_size:
            select += f"LIMIT {page_size} OFFSET {num_of_element_to_skip}"

        log.debug(f"{select} {values}")
        list_of_items = self._cursor.execute(select, values).fetchall()

        cursor_desc_copy = copy.deepcopy(self._cursor.description)

        # Get the total
        if not page_size:
            response.total = len(list_of_items)

        self._fill_response_with_item(response, list_of_items, cursor_desc_copy)
        return response
