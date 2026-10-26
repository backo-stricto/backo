# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for SQL db connector
"""

from abc import ABC, abstractmethod
from typing import Self, Any


class SqlFieldDescription(ABC):
    """
    Description of a Field, in SQL and Backo
    """

    db_path: str = None
    """ The name of the field """

    _sql_type: str = None
    """ The SQL Type"""

    _cid: int = 0
    """ The column number"""

    _not_null: bool = False
    """ If required or not """

    _dflt_value = None
    """ the default value if exists """

    _pk: bool = False
    """ If the field is a key """

    _ref_table: str = None
    """ The reference table """

    _ref_field: str = None
    """ The reference field in _ref_table """

    def __init__(self):

        self.db_path: str = None
        self._sql_type: str = None
        self._cid: int = 0
        self._not_null: bool = False
        self._dflt_value = None
        self._pk: bool = False
        self._ref_table: str = None
        self._ref_field: str = None

    def __repr__(self):
        return f"Sqlfield({self.db_path}, {self._sql_type}, {self._pk}, not_null={self._not_null}, default={self._dflt_value} -> {self._ref_table}/{self._ref_field})"

    @abstractmethod
    def get_type_from_backo(self, backo_types: list[str]) -> str:
        """
        Return the SQlite3 type for this backo type

        :param backo_types: like [ 'Int', 'GenericType' ]
        :type backo_types: list[str]
        :raises DBError: If the backo type is not implemented into the Sqlite3
        :return: SQL_TYPE_MAPPER
        :rtype: str
        """

    def get_drop_pragma(self, _table_name: str = None) -> str:
        """
        Return the SLite3 command for droping this key

        :return: a DROP... string
        :rtype: str
        """
        return f"DROP COLUMN {self.db_path}"

    def get_add_pragma(self, _table_name: str = None) -> str:
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
        if self._dflt_value:
            f += f" DEFAULT {self._dflt_value}"
        if self._ref_table:
            f += f",\r\n  FOREIGN KEY {self.db_path} REFERENCES {self._ref_table}({self._ref_field})"

        return f

    def get_create_pragma(self, _table_name: str = None) -> str:
        """
        Return the CREATE sqlite3 command for a table

        :return: the CREATE... command
        :rtype: str
        """
        f = f"{self.db_path} {self._sql_type}"
        if self._not_null:
            f += " NOT NULL"
        if self._dflt_value:
            f += f" DEFAULT {self._dflt_value}"
        if self._pk:
            f += " PRIMARY KEY AUTOINCREMENT"
        return f

    def get_post_pragma(self, _table_name: str = None) -> str:
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
            return False
        if self._sql_type != other._sql_type:
            return False
        if self._ref_table != other._ref_table:
            return False
        if self._ref_field != other._ref_field:
            return False
        if self._dflt_value != other._dflt_value:
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
        ]:
            setattr(self, att, getattr(self, att) or getattr(other, att))

    def fill_from_backo(self, db_path: str, shema: dict = {}):
        """
        fill the backo meta_data

        :param db_path: the path name
        :type db_path: str
        :param shema: the metadata for this field, defaults to {}
        :type shema: dict, optional
        """
        self.db_path = db_path

        if shema and "types" in shema:
            self._sql_type = self.get_type_from_backo(shema["types"])
            if shema["required"] is True:
                self._not_null = True

    def fill_from_db_pragma( # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        cid: int,
        db_path: str,
        sql_type: str,
        not_null: bool,
        pk: bool,
        dflt_value: Any,
        ref_table: str,
        ref_field: str,
    ) -> None:
        """
        Fill from data read in the database

        :param cid: The column number
        :type cid: int
        :param db_path: The name of the field
        :type db_path: str
        :param sql_type: the default value if exists
        :type sql_type: str
        :param not_null: If required or not
        :type not_null: bool
        :param pk: If the field is a key
        :type pk: bool
        :param dflt_value: Default value if exists
        :type dflt_value: Any
        :param ref_table: The reference table
        :type ref_table: str
        :param ref_field: The reference field in _ref_table
        :type ref_field: str
        """

        self.db_path = db_path
        self._sql_type = sql_type
        self._cid = cid
        self._not_null = not_null
        self._dflt_value = dflt_value
        self._pk = pk
        self._ref_table = ref_table
        self._ref_field = ref_field
