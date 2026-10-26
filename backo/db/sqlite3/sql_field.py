# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""

from ..sql.sql_field import SqlFieldDescription

from ...error import DBError


SQL_TYPE_MAPPER = {
    "String": "TEXT",
    "Int": "INTEGER",
    "Bool": "INTEGER",
    "Float": "REAL",
    "Datetime": "DATE",
    "Ref": "TEXT",
    "List": "TEXT",
    "RefsList": "TEXT",
    "Dict": "TEXT",
    "Tuple": "TEXT",
}


# If backo gives a required= into a field without a default, must add a default
# in SQlite3 because it doesnt want a NOT NULL field without DEFAULT
SQL_TYPE_DEFAULT = {
    "TEXT": "",
    "INTEGER": "0",
    "REAL": "0.0",
    "DATE": "",
}


class SQlite3FieldDescription(SqlFieldDescription):
    """
    Specific SqlFieldDescription for SQlite3

    :param SqlFieldDescription: _description_
    :type SqlFieldDescription: _type_
    """

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

    def fill_from_backo(self, db_path: str, shema: dict = {}):
        """
        fill the backo meta_data

        :param db_path: the path name
        :type db_path: str
        :param shema: the metadata for this field, defaults to {}
        :type shema: dict, optional
        """
        super().fill_from_backo(db_path, shema)
        if self._not_null:
            if "default" in shema and shema["default"] is not None:
                self._dflt_value = shema["default"]
            else:
                self._dflt_value = SQL_TYPE_DEFAULT[self._sql_type]
