# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut Filter
"""

from typing import Any, Callable

from stricto import SFilter

class Filter():
    """
    Filter transformation for sqlite3

    """

    def __init__(
        self,
        get_transformer: Callable
    ):
        """

        """
        self.model = None
        self.get_transformer = get_transformer

    def set_model( self, scheme: dict )->None:
        self.model = scheme['item']

    def build_db_filter(self, backo_filter: SFilter)-> Any:
        pass