# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut Filter
"""

from typing import Any, Callable
from enum import Enum, auto

from stricto import SFilter
from ...error import DBError
from ...sort import Sort


class FilterReport(Enum):
    """
    Specify the report of the filter

    """

    EXACT = auto()
    """ The filter transposition into the DB will return exactly the SFilter wanted """
    MORE = auto()
    """ The filter transposition into the DB will return more element the SFilter wanted """
    LESS = auto()
    """ The filter transposition into the DB will return less element the SFilter wanted """

    def __repr__(self):
        return self.name


class Filter:
    """
    Filter transformation to transform a SFilter into a filter for the Database

    """

    def __init__(self, get_transformer: Callable):
        """ """
        self.model = None
        self.get_transformer = get_transformer

    def set_model(self, model: dict) -> None:
        """
        Set the model (meta() to the filter), to adapt
        the filtering on types of objects

        :param model: scheme
        :type model: dict
        """
        self.model = model

    def _get_model_by_path(self, path: str, key_path: list[str], model: dict) -> dict:
        """
        Return the corresponding model to check if the path dont go out of the model

        :param path: the path as string (like '$.address.street' )
        :type path: str
        :param key_path: the path (like [ 'address', 'steet' ])
        :type key_path: list[str]
        :param model: the backo model
        :type model: dict
        :return: the corresponding sub model
        :rtype: dict
        """
        if not key_path:
            return model

        # A Dict
        if "sub_scheme" in model:
            sub_model = model["sub_scheme"]
            p = key_path.pop(0)
            if not p in sub_model:
                raise DBError("Wrong path {0} (doesnt exists in model)", path)
            return self._get_model_by_path(path, key_path, sub_model[p])

        # A List
        if "sub_type" in model:
            raise DBError("Filter in list not implemented (path={0})", path)

        if "sub_types" in model:
            raise DBError("Filter in tuples not implemented (path={0})", path)

        raise DBError("Wrong path {0} (doesnt exists in model)", path)

    def build_db_filter(self, backo_filter: SFilter) -> tuple[Any, FilterReport]:
        """
        Transform a SFilter into a filter for the DB

        :param backo_filter: _description_
        :type backo_filter: SFilter
        :return: the filter for the DB and a Filter Report
        :rtype: tuple [ Any, FilterReport ]
        """

    def build_db_projection(self, _backo_projection: list[str]) -> Any:
        """
        Transform a SFilter into a filter for the DB

        :param backo_filter: the SFilter
        :type backo_filter: SFilter
        :return: a filter available to the DB
        :rtype: Any
        """
        return None

    def build_db_sort(self, _backo_sort: Sort) -> Any:
        """
        Transform a Sort into a sort command available for this DB

        :param _backo_sort: the Sort
        :type _backo_sort: Sort
        :return: a order available to the DB
        :rtype: Any
        """
        return None
