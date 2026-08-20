# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""



from stricto import SFilter


class Filter():
    """
    Filter transformation for sqlite3

    """

    def __init__(
        self,
        table_name: str,
        backo_filter: SFilter,
        model: dict,
    ):
        """

        """
        self._table_name = table_name
        self.backo_filter = backo_filter
        self.model = model


    def build_db_filter(self):
        pass