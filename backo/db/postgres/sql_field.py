# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Sql field description (pragma) for postgress
"""

from ..sql.sql_field import SqlFieldDescription

from ...error import DBError

SQL_TYPE_MAPPER = {
    "String": "VARCHAR",
    "Int": "BIGINT",
    "Bool": "BOOLEAN",
    "Float": "DOUBLE PRECISION",
    "Datetime": "TIMESTAMPTZ",
    "Ref": "VARCHAR",
    "Id": "UUID",
}

SQL_REVERSE_MAPPER = {
    "UUID": "UUID",
    "SMALLINT": "INT2",
    "INTEGER": "INT4",
    "BIGINT": "BIGINT",
    "REAL": "FLOAT4",
    "DOUBLE PRECISION": "DOUBLE PRECISION",
    "BOOLEAN": "BOOLEAN",
    "CHARACTER VARYING": "VARCHAR",
    "CHARACTER": "BPCHAR",
    "TIMESTAMP WITH TIME ZONE": "TIMESTAMPTZ",
    "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
    "TIME WITH TIME ZONE": "TIMETZ",
    "TIME WITHOUT TIME ZONE": "TIME",
    "NUMERIC": "DECIMAL",
    "BIT VARYING": "VARBIT",
}


class PostgresFieldDescription(SqlFieldDescription):
    """
    Specific SqlFieldDescription for Postgress

    """

    def fill_from_pragma(
        self, current_pragma: tuple[str, str, bool, bool, bool, str, str, str]
    ):
        """
        Fill direclty from the select into postgres

        :param current_pragma: name, type, required, pk, fk, default_value, referenced_table, referenced_column
        :type current_pragma: tuple[str, str, bool, bool, bool, str, str, str]
        """
        self.fill_from_db_pragma(
            cid=0,
            db_path=current_pragma[0],
            sql_type=SQL_REVERSE_MAPPER[current_pragma[1]],
            not_null=current_pragma[2],
            pk=current_pragma[3],
            dflt_value=None,
            ref_table=current_pragma[6],
            ref_field=current_pragma[7],
        )

    def get_type_from_backo(self, backo_types: list[str]) -> str:
        """
        Return the SQlite3 type for this backo type

        :param backo_types: like [ 'Int', 'GenericType' ]
        :type backo_types: list[str]
        :raises DBError: If the backo type is not implemented into the Sqlite3
        :return: SQL_TYPE_MAPPER
        :rtype: str
        """
        for backo_type in backo_types:
            if backo_type in SQL_TYPE_MAPPER:
                return SQL_TYPE_MAPPER[backo_type]

        raise DBError("Backo type {0} not implemented in Sqlite3", backo_types)

    def get_create_pragma(self, _table_name: str = None) -> str:
        """
        Return the CREATE sqlite3 command for a table

        :return: the CREATE... command
        :rtype: str
        """
        f = f"{self.db_path} {self._sql_type}"
        if self._not_null:
            f += " NOT NULL"
        if self._dflt_value is not None:
            print(f" default = {self._dflt_value} ({type(self._dflt_value)})")
            f += f" DEFAULT {self._dflt_value}"
        if self._pk:
            f += " PRIMARY KEY DEFAULT gen_random_uuid()"
        if self._ref_table:
            f += f",\r\nCONSTRAINT {self.db_path} FOREIGN KEY ({self.db_path}) REFERENCES {self._ref_table}({self._ref_field})"

        return f

    def get_add_pragma(self, table_name: str = None) -> str:
        """
        Return the ADD sqlite3 command for adding a key

        :return: the ADD... command
        :rtype: str
        """
        f = f"ADD COLUMN {self.db_path} {self._sql_type}"
        if self._not_null:
            f += " NOT NULL"
        if self._pk:
            f += " PRIMARY KEY DEFAULT gen_random_uuid()"
        if self._dflt_value:
            f += f" DEFAULT {self._dflt_value}"
        f += ";"
        if self._ref_table:
            f += f"\r\nALTER TABLE {table_name} ADD CONSTRAINT {self.db_path} FOREIGN KEY ({self.db_path}) REFERENCES {self._ref_table}({self._ref_field})"

        return f

    def get_post_pragma(self, _table_name: str = None) -> str:
        return ""
