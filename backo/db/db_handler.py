"""
Module providing the Generic() Class for connection on DB
"""

import uuid
import sys
from typing import Callable, Any
from abc import ABC, abstractmethod

# used for developpement
sys.path.insert(1, "../../../stricto")

from stricto import Kparse, SFilter

from .request import (
    Response,
    SearchRequest,
    SelectRequest,
    UpdateRequest,
    DeleteRequest,
    CreateRequest,
)
from .item_mapper import ItemMapper

KPARSE_MODEL = {"restriction": Callable}


class DBHandler(ABC):  # pylint: disable=too-many-instance-attributes
    """Database Connector

    This is the way to save / store / retrieve objects

    :param ``**kwargs``:
        - *restriction=* ``func`` --
          not used yet


    """

    def __init__(self, db_name: str, item_mapper: ItemMapper = None, **kwargs):
        """Constructor"""

        self._name = db_name
        self.item_mapper = item_mapper

        options = Kparse(kwargs, KPARSE_MODEL)

        self.restriction_filter = options.get("restriction")

    @abstractmethod
    def drop(self):  # pylint: disable=unused-argument
        """Drop the collection

        Mainly used in test


        :raise Error: Raise an error DBError or any db error
        """

    @abstractmethod
    def db_search(self, db_request: SearchRequest) -> Response:
        """get one"""
        return None

    @abstractmethod
    def db_delete(self, db_request: DeleteRequest) -> Response:
        """delete"""
        return None

    @abstractmethod
    def db_update(self, db_request: UpdateRequest) -> Response:
        """update one"""
        return None

    @abstractmethod
    def db_select(self, db_request: SelectRequest) -> Response:
        """select"""
        return None

    @abstractmethod
    def db_create(self, db_request: CreateRequest) -> Response:
        """select"""
        return None

    @abstractmethod
    def db_build_select_request(self, request: SelectRequest) -> Any:
        """
        build the request

        :return: _description_
        :rtype: Any
        """

    @abstractmethod
    def db_build_search_request(self, request: SearchRequest) -> Any:
        """
        build the request

        :return: _description_
        :rtype: Any
        """

    @abstractmethod
    def db_build_update_request(self, request: UpdateRequest) -> Any:
        """
        build the request

        :return: _description_
        :rtype: Any
        """

    @abstractmethod
    def db_build_create_request(self, request: CreateRequest) -> Any:
        """
        build the request

        :return: _description_
        :rtype: Any
        """

    @abstractmethod
    def db_build_delete_request(self, request: DeleteRequest) -> Any:
        """
        build the request

        :return: _description_
        :rtype: Any
        """

    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """

    def close(self):
        """Close the mongodb connection

        :raise DBError: Raise an error in case of database Error

        """

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        Mainly, not used, because the database itself do the job (like mongo).
        But for other cases, you must generate by yourself the uniq *_id* for the object

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        return str(uuid.uuid4().int >> 64)

    def get_by_id(self, _id: str) -> dict:  # pylint: disable=unused-argument
        """
        get an object by _id in the DB and return it

        :param _id: the _id
        :type _id: str
        :return: The object (json format)
        :rtype: dict
        :raise Error: Raise an error DBError or any db error

        """
        req = SearchRequest(_id)
        data = self.db_search(self.db_build_search_request(req))
        resp = Response()
        if self.item_mapper:
            self.item_mapper.do_post_read(data)
        resp.data = data
        return resp.data

    def create(self, o: Any) -> str:  # pylint: disable=unused-argument
        """Create the object into the DB and return the _id

        :param o: The object given (json format)
        :type o: dict
        :raise Error: Raise an error DBError or any db error

        """

        if self.item_mapper:
            self.item_mapper.do_pre_write(o)

        req = CreateRequest(o)
        data = self.db_create(self.db_build_create_request(req))
        resp = Response()
        resp.data = data
        return resp.data

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        """Save the objet

        :param _id: the _id of this object
        :type _id: str
        :param o: The object given (json format)
        :type o: dict
        :raise Error: Raise an error DBError or any db error

        """

        if self.item_mapper:
            self.item_mapper.do_pre_write(o)

        req = UpdateRequest(_id, o)
        data = self.db_update(self.db_build_update_request(req))
        resp = Response()
        resp.data = data
        return resp.data

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        """The _id to delete on the db

        :param _id: the _id
        :type _id: str
        :raise Error: Raise an error DBError or any db error
        """
        req = DeleteRequest(_id)
        data = self.db_delete(self.db_build_delete_request(req))
        resp = Response()
        resp.data = data
        return resp.data

    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter,
        projection: list[str] = [],
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: dict = {},
    ) -> Response:
        """
        Select from filter in the DB and return a list of dicts, with pagination

        :param select_filter: The filter for selection (depends on DB types)
        :param projection: The list of elements we want for each object
        :type projection: dict
        :param page_size: number of elements per page
        :type page_size: int
        :param num_of_element_to_skip: number of element to skip from beginning
        :type num_of_element_to_skip: int
        :param sort_object: Soon
        :type sort_object: dict
        :raise Error: Raise an error DBError or any db error

        """
        req = SelectRequest(select_filter, projection)
        data = self.db_select(self.db_build_select_request(req))
        resp = Response()
        if self.item_mapper:
            if isinstance(data, list):
                for d in data:
                    self.item_mapper.do_post_read(d)

        resp.data = data
        return resp.data
