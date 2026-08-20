# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""

from typing import Self

SQL_TYPE_MAPPER = {
    "String": "TEXT",
    "Int": "INTEGER",
    "Bool": "INTEGER",
    "Float": "REAL",
    "Datetime": "INTEGER",
    "Ref": "TEXT",
    "List": "TEXT",
    "RefsList": "TEXT",
    "Dict": "TEXT",
    "Tuple": "TEXT",
}


class SqlFieldDescription:
    """
    Description of a Field, il SQL and Backo
    """

    def __init__(
        self,
        current_pragma: tuple[int, str, str, int, str, int] = None,
        foreign_key: tuple[int, int, str, str, str, str, str, str] = None,
    ):
        """


        :param current_pragma: data comes from "pragma" slite3 command, defaults to None
        :type current_pragma: tuple[int, str, str, int, str, int], optional
        :param foreign_key: data comes from "pragma" slite3 command, defaults to None
        :type foreign_key: tuple[int, int, str, str, str, str, str, str], optional
        """
        self.db_path = None
        self._sql_type = None
        self._cid = 0
        self._not_null = False
        self._dflt_value = None
        self._pk = False
        self._ref_table = None
        self._ref_field = None
        self._on_update = None
        self._on_delete = None
        self._match = None
        self._fkid = 0
        self._seq = 0

        if current_pragma:
            (
                self._cid,
                self.db_path,
                self._sql_type,
                not_null_as_int,
                self._dflt_value,
                pk,
            ) = current_pragma
            self._pk = bool(pk)
            self._not_null = bool(not_null_as_int)

        if foreign_key:
            (
                self._fkid,
                self._seq,
                self._ref_table,
                self.db_path,
                self._ref_field,
                self._on_update,
                self._on_delete,
                self._match,
            ) = foreign_key

    def get_drop_pragma(self) -> str:
        """
        Return the SLite3 command for droping this key

        :return: a DROP... string
        :rtype: str
        """
        return f"DROP COLUMN {self.db_path}"

    def get_add_pragma(self) -> str:
        """
        Return the ADD sqlite3 command for adding a key

        :return: the ADD... command
        :rtype: str
        """
        f = f"ADD COLUMN {self.db_path} {self._sql_type}"
        if self._not_null:
            f += " NOT NULL"
        if self._pk:
            f += " PRIMARY KEY AUTOINCREMENT"
        if self._ref_table:
            f += f",\r\n  FOREIGN KEY {self.db_path} REFERENCES {self._ref_table}({self._ref_field})"

        return f

    def get_create_pragma(self) -> str:
        """
        Return the CREATE sqlite3 command for a table

        :return: the CREATE... command
        :rtype: str
        """
        f = f"{self.db_path} {self._sql_type}"
        if self._not_null:
            f += " NOT NULL"
        if self._pk:
            f += " PRIMARY KEY AUTOINCREMENT"
        return f

    def get_post_pragma(self) -> str:
        """
        Return the end of the creation / modification command for foreigh keys.

        :return: return FOREIGN... string
        :rtype: str
        """
        if self._ref_table:
            return f"FOREIGN KEY ({self.db_path}) REFERENCES {self._ref_table}({self._ref_field})"
        return ""

    def equal(self, other: Self) -> bool:
        """
        Return True if the both fields are equals

        :param other: _description_
        :type other: Self
        :return: _description_
        :rtype: bool
        """
        if self._not_null != other._not_null:
            # print(f"not equal for {self.db_path} not_null")
            return False
        if self._sql_type != other._sql_type:
            # print(
            #     f"not equal for {self.db_path} _sql_type {self._sql_type} != {other._sql_type}"
            # )
            return False
        if self._ref_table != other._ref_table:
            # print(f"not equal for {self.db_path} _ref_table")
            return False
        if self._ref_field != other._ref_field:
            # print(f"not equal for {self.db_path} _ref_field")
            return False
        return True

    def merge(self, other: Self):
        """
        merge fields

        :param other: the second to merge into the first
        :type other: Self
        """
        for att in [
            "db_path",
            "_sql_type",
            "_cid",
            "_not_null",
            "_dflt_value",
            "_pk",
            "_ref_table",
            "_ref_field",
            "_on_update",
            "_on_delete",
            "_match",
            "_fkid",
            "_seq",
        ]:
            setattr(self, att, getattr(self, att) or getattr(other, att))

    def create(self, db_path: str, shema: dict = {}):
        """
        fill the backo meta_data

        :param db_path: the path name
        :type db_path: str
        :param shema: the metadata for this field, defaults to {}
        :type shema: dict, optional
        """
        self.db_path = db_path

        if shema and "types" in shema:
            for backo_type in shema["types"]:
                if backo_type in SQL_TYPE_MAPPER:
                    self._sql_type = SQL_TYPE_MAPPER[backo_type]
                    if shema["required"] is True:
                        self._not_null = True


class TablePragma:
    """
    Metadata for a sqlite3 table
    """

    def __init__(self, table_name: str):
        """

        :param table_name: the name of the table
        :type table_name: str
        """
        self._name = table_name

        self.backo_fields: dict[str, SqlFieldDescription] = {}
        self.db_fields: dict[str, SqlFieldDescription] = {}

    def add_backo_field(self, f: SqlFieldDescription):
        """
        Add a backo field

        :param f: the field
        :type f: SqlFieldDescription
        """
        db_path = f.db_path

        self.backo_fields[db_path] = f

    def add_db_field(self, f: SqlFieldDescription):
        """
        Add a sqlite3 field

        :param f: the field
        :type f: SqlFieldDescription
        """
        db_path = f.db_path
        if db_path not in self.db_fields:
            self.db_fields[db_path] = f
            return

        self.db_fields[db_path].merge(f)

    def get_create_pragma(self) -> str:
        """
        Return all informations for creation of a table

        :return: the creation string
        :rtype: str
        """
        f = f"CREATE TABLE {self._name} (\r\n  "
        s = []
        for p in self.backo_fields.values():
            s.append(p.get_create_pragma())
        for p in self.backo_fields.values():
            post = p.get_post_pragma()
            if post:
                s.append(p.get_post_pragma())
        f += ",\r\n  ".join(s)
        f += " );\r\n"
        return f

    def get_modification_pragma(self) -> str:
        """
        return the string for altering an existing table

        :return: the ALTER... string
        :rtype: str
        """

        suffix = f"ALTER TABLE {self._name}  "
        s = []

        seen_in_old = []
        # Chekc pragmas from backo and try to find new and modified ont
        for p in self.backo_fields.values():
            # A new Field
            if p.db_path not in self.db_fields:
                s.append(f"{suffix}  {p.get_add_pragma()} {p.get_post_pragma()};")
                continue
            seen_in_old.append(p.db_path)

            # = Or modified fiend
            cp = self.db_fields[p.db_path]
            if p.equal(cp) is False:
                s.append(f"{suffix}  {cp.get_drop_pragma() };")
                s.append(f"{suffix}  {p.get_add_pragma() } {p.get_post_pragma()};")

        for cp in self.db_fields.values():
            if cp.db_path not in seen_in_old:
                s.append(f"{suffix}  {cp.get_drop_pragma()};")

        if len(s) == 0:
            return None

        return "\r\n".join(s)

    def get_pragma(self) -> str:
        """
        Return the creation or modification string

        :return: the string to copy past for creation
        :rtype: str
        """
        if len(self.db_fields.keys()) == 0:
            return self.get_create_pragma()
        return self.get_modification_pragma()
