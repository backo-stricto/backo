"""
request and response definitions
"""

# pylint: disable=too-few-public-methods
import sys
from abc import ABC
from typing import Any, Self

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

    def __init__(self, _id: str, data: dict):
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

    def __init__(self, data: dict):
        self._data = data
        super().__init__()


class SelectRequest(Request):
    """
    Abstract class for a select request

    """

    def __init__(self, sfilter: SFilter = None, projection: list[str] = [], page_size: int = 0, num_of_element_to_skip: int = 0, sort=None):

        self._filter = sfilter
        self._projection = projection
        self._page_size = page_size
        self._num_of_element_to_skip = num_of_element_to_skip
        self._sort= sort

        super().__init__()


class Response(RequestResponse):
    """
    A response from the connector to backo
    """

    def __init__(self):
        self.data = None
        self.filter_completed = False
        self.stats = None
        super().__init__()




class New_Request():

    childs_requests : list [ Self ]

    def __init__(self):
       self.childs_requests = []
    

    def get(self)-> Any:
        """ return the request as something understandable """



class Create_Request(New_Request):

    def __init__(self, table_name: str):
     """
    :param _id: The _id to search
     :type _id: str
     """
     self.table_name = table_name
     print(f'create table request {table_name}')
     super().__init__()

    def append( self, key:str, value:Any )-> None:
        """ Add values to the query """
        return


class Update_Request(New_Request):

    def __init__(self, table_name: str):
     """
    :param _id: The _id to search
     :type _id: str
     """
     self.table_name = table_name
     super().__init__()

    def append( self, key:str, value:Any )-> None:
        """ Add values to the query """
        return

class Search_Request(New_Request):

    def __init__(self, table_name: str, _id: str):
     """
    :param _id: The _id to search
     :type _id: str
     """
     self.table_name = table_name
     self._id = _id
     super().__init__()

class Delete_Request(New_Request):

    def __init__(self, table_name: str, _id: str):
     """
    :param _id: The _id to search
     :type _id: str
     """
     self.table_name = table_name
     self._id = _id
     super().__init__()

class Select_Request(New_Request):

    def __init__(self, table_name: str, filter: Any):
     """
    :param _id: The _id to search
     :type _id: str
     """
     self.table_name = table_name
     self.filter = filter
     super().__init__()
