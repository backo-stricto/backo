# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for sql db connector
"""

import re


from ...attribute_mapper import AttributeMapper

from .pragma import SqlFieldDescription, TablePragma, SqlDBChecker

class Sqlite3AttributeMapper(AttributeMapper):
    """
    Attribut Mapper specific for Sqlite3

    ust to rewrite the path for filtering, projection...

    """

    def _path_to_table_field(self, path: str) -> str:
        """
        return the same path without "$."
        """
        # drop $. at the beginning
        a = re.sub(r"^\$\.", "", path)
        # change . into _
        return re.sub(r"\.|\$", "_", a)

    def get_sub_table_name( self, table_name: str,  path: str)-> str:
        return "Unknown"

    def get_for_projection(self, path: str) -> str:
        """
        return the attribut name when asked for the projection
        """
        return self._path_to_table_field(path)

    def get_for_filter(self, path: str) -> str:
        """
        return the attribut name when asked for the filter
        """
        return self._path_to_table_field(path)

    def get_field_description(self, table_name: str, path: str, shema: dict):

        f = SqlFieldDescription()
        f.create(self._path_to_table_field(path), shema)

        # Get the singleton
        checker = SqlDBChecker()
        tp = checker.get_table(table_name)
        tp.add_backo_field(f)


class Sqlite3ListAttributeMapper(Sqlite3AttributeMapper):
    """
    Attribut Mapper specific for Sqlite3 for a List

    ust to rewrite the path for filtering, projection...

    """


    def get_sub_table_name(self, table_name:str, path: str)-> str:
        """
        list are stored in a secondary table.

        this is the build if the name of the secondart table
        :param table_name: the main table name
        :type table_name: str
        :param path: the field name
        :type path: str
        :return: the new table name
        :rtype: str
        """
        db_name = self._path_to_table_field(path)
        return f"{table_name}_{db_name}"


    def get_field_description(self, table_name: str, path: str, shema: dict):

        db_name = self._path_to_table_field(path)
        sub_table_name = f"{table_name}_{db_name}"

        # Get the singleton
        checker = SqlDBChecker()
        tp = checker.get_table(sub_table_name)
        if tp is None:
            tp = TablePragma(sub_table_name)
            checker.add_table(tp)

        f1 = SqlFieldDescription()
        f1.create(f"{table_name}_id", {"types": ["Int"], "required": False})
        f1._ref_table = table_name
        f1._ref_field = "id"
        tp.add_backo_field(f1)

        checker._fill_table_informations(sub_table_name, {"$": shema["sub_type"]})


class Sqlite3RefsListAttributeMapper(Sqlite3AttributeMapper):
    """
    Attribut Mapper specific for Sqlite3 for a RefsList

    ust to rewrite the path for filtering, projection...

    """


    def get_field_description(self, table_name: str, path: str, shema: dict):

        db_name = self._path_to_table_field(path)

        db_reverse = self._path_to_table_field(shema["reverse"])

        sub_table_name_as_list = [
            f"{table_name}_{db_name}",
            f'{shema["collection"]}_{db_reverse}',
        ]
        sub_table_name_as_list.sort()
        sub_table_name = "_".join(sub_table_name_as_list)

        # Get the singleton
        checker = SqlDBChecker()

        tp = checker.get_table(sub_table_name)
        if tp is None:
            tp = TablePragma(sub_table_name)
            checker.add_table(tp)

        f1 = SqlFieldDescription()
        f1.create(f'{shema["collection"]}_id', {"types": ["Int"], "required": False})
        f1._ref_table = shema["collection"]
        f1._ref_field = "id"
        tp.add_backo_field(f1)

        f2 = SqlFieldDescription()
        f2.create(f"{table_name}_id", {"types": ["Int"], "required": False})
        f2._ref_table = table_name
        f2._ref_field = "id"
        tp.add_backo_field(f2)

        checker._fill_table_informations(sub_table_name, {})


class Sqlite3RefAttributeMapper(Sqlite3AttributeMapper):
    """
    Attribut Mapper specific for Sqlite3 for a List

    ust to rewrite the path for filtering, projection...

    """

    def get_field_description(self, table_name: str, path: str, shema: dict):
        return


class Sqlite3_idAttributeMapper(Sqlite3AttributeMapper):
    """
    Attribut Mapper specific for Sqlite3 for a List

    ust to rewrite the path for filtering, projection...

    """

    def get_field_description(self, table_name: str, path: str, shema: dict):

        f = SqlFieldDescription()
        f.create("id", {"types": ["Int"], "required": False})
        f._pk = True

        # Get the singleton
        checker = SqlDBChecker()
        tp = checker.get_table(table_name)
        tp.add_backo_field(f)


class Sqlite3DictAttributeMapper(Sqlite3AttributeMapper):
    """
    Attribut Mapper specific for Sqlite3 for a List

    ust to rewrite the path for filtering, projection...

    """

    def get_field_description(self, table_name: str, path: str, shema: dict) -> None:

        # Get the singleton
        checker = SqlDBChecker()

        for field_shema in shema["sub_scheme"].values():

            mapper = checker.db_handler.item_mapper.get_mapper(
                field_shema["path"], field_shema["types"]
            )
            mapper.get_field_description(table_name, field_shema["path"], field_shema)

