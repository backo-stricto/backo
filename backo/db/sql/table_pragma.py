# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""

from .sql_field import SqlFieldDescription


class TablePragma:
    """
    Metadata for a sql table
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
            s.append(p.get_create_pragma(self._name))
        for p in self.backo_fields.values():
            post = p.get_post_pragma(self._name)
            if post:
                s.append(p.get_post_pragma(self._name))
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
                s.append(
                    f"{suffix}  {p.get_add_pragma(self._name)} {p.get_post_pragma(self._name)};"
                )
                continue
            seen_in_old.append(p.db_path)

            # = Or modified fiend
            cp = self.db_fields[p.db_path]
            if p.equal(cp) is False:
                s.append(f"{suffix}  {cp.get_drop_pragma(self._name) };")
                s.append(
                    f"{suffix}  {p.get_add_pragma(self._name) } {p.get_post_pragma(self._name)};"
                )

        for cp in self.db_fields.values():
            if cp.db_path not in seen_in_old:
                s.append(f"{suffix}  {cp.get_drop_pragma(self._name)};")

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
