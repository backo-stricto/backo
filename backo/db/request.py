"""
request and response definitions
"""

# pylint: disable=too-few-public-methods
import sys
from abc import ABC
from typing import Any

# used for developpement
sys.path.insert(1, "../../../stricto")
from stricto import SFilter


class RequestResponse(ABC):
    """
    Abstract class for request AND responses
    """


class Request(RequestResponse):
    """
    Abstract class for request

    """

    def build_filter(self, sfilter: SFilter) -> Any:
        """
        Transform the backo filter (SFilter) into a comprehensive filter to the DB

        :param filter: _description_
        :type filter: SFilter
        :return: _description_
        :rtype: Any
        """


class SearchRequest(Request):
    """
    Search (get by id) request

    """

    def __init__(self, _id: str):
        """

        :param _id: The _id to search
        :type _id: str
        """
        self._id = _id
        super().__init__()


class DeleteRequest(Request):
    """
    Delete by id request

    """

    def __init__(self, _id: str):
        """

        :param _id: The id to delete
        :type _id: str
        """
        self._id = _id
        super().__init__()


class UpdateRequest(Request):
    """
    Update request ( save )

    """

    def __init__(self, _id: str, data: Any):
        """

        :param _id: The id of the object
        :type _id: str
        :param data: The object
        :type data: Any
        """
        self._id = _id
        self._data = data
        super().__init__()


class CreateRequest(Request):
    """
    Abstract class for a creation request

    """

    def __init__(self, data: Any):
        self._data = data
        super().__init__()


class SelectRequest(Request):
    """
    Abstract class for a select request

    """

    def __init__(self, sfilter: SFilter = None, projection: list[str] = []):

        self._filter = sfilter
        self._projection = projection

        super().__init__()


class Response(RequestResponse):
    """
    A response from the connector to backo
    """

    def __init__(self):
        self.data = None
        self.filter_completed = False

        super().__init__()
