# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut Filter
"""

from typing import Any, Callable

from stricto import SFilter


class Filter:
    """
    Filter transformation for sqlite3

    """

    def __init__(self, get_transformer: Callable):
        """ """
        self.model = None
        self.get_transformer = get_transformer

    def set_model(self, scheme: dict) -> None:
        """
        Set the model (meta() to the filter), to adapt
        the filtering on types of objects

        :param scheme: scheme
        :type scheme: dict
        """
        self.model = scheme["item"]

    def build_db_filter(self, backo_filter: SFilter) -> Any:
        """
        Transform a SFilter into a filter for the DB

        :param backo_filter: the SFilter
        :type backo_filter: SFilter
        :return: a filter available to the DB
        :rtype: Any
        """
