# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut Filter
"""

from typing import Any, Callable

from stricto import SFilter
from ...error import DBError


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

    def build_db_filter(self, backo_filter: SFilter) -> Any:
        """
        Transform a SFilter into a filter for the DB

        :param backo_filter: the SFilter
        :type backo_filter: SFilter
        :return: a filter available to the DB
        :rtype: Any
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
