# pylint: disable=relative-beyond-top-level
"""
Memory DB Connector
"""

import uuid
from typing import Any
import copy
from ..db_handler import DBHandler
from ..item_mapper import ItemMapper
from ...error import NotFoundError
from ..request import (
    DeleteRequest,
    UpdateRequest,
    CreateRequest,
    SearchRequest,
    SelectRequest,
)


class DBMemoryConnector(DBHandler):
    """
    A memory storage (in a dict)
    """

    def __init__(self, db_name: str, item_handler: ItemMapper = ItemMapper(), **kwargs):
        """

        :param db_name: Name of th DB
        :type db_name: str
        :param item_handler: _description_, defaults to ItemMapper()
        :type item_handler: ItemMapper, optional
        """

        self._datas: dict[str, dict] = {}

        super().__init__(db_name, item_handler, **kwargs)

    def drop(self) -> None:
        """
        Drop all datas
        """
        self._datas = {}

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

    def db_build_search_request(self, request: SearchRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: SearchRequest
        :return: the understandable version of the request for thos connector
        :rtype: Any
        """
        return request._id

    def db_search(self, _id: str) -> Any:
        """get one"""

        d = copy.deepcopy(self._datas.get(_id))
        if not d:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)
        return d

    def db_build_delete_request(self, request: DeleteRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: DeleteRequest
        :return: the understandable version of the request for this connector
        :rtype: Any
        """

        return request._id

    def db_delete(self, _id: str) -> Any:
        """delete"""
        if _id not in self._datas:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        del self._datas[_id]
        return True

    def db_build_update_request(self, request: UpdateRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: UpdateRequest
        :return: the understandable version of the request for this connector
        :rtype: Any
        """
        return request._id, request._data

    def db_update(self, _id: str, data: dict) -> Any:
        """update one"""
        if _id not in self._datas:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        d = copy.deepcopy(data)
        d[_id] = _id
        self._datas[_id] = d
        return d

    def db_build_select_request(self, request: SelectRequest) -> Any:
        """
        build the request

        :param request: the SelectRequest
        :type request: UpdateRequest
        :return: the understandable version of the request for this connector
        :rtype: Any
        """
        return request._filter, request._projection

    def db_select(self, db_request: Any) -> Any:  # pylint: disable=unused-argument
        """select"""
        a = []
        for d in self._datas.values():
            a.append(d)
        return a

    def db_build_create_request(self, request: CreateRequest) -> Any:
        """
        build the request

        :param request: the CreateRequest
        :type request: UpdateRequest
        :return: the understandable version of the request for this connector
        :rtype: Any
        """
        return request._data

    def db_create(self, data: Any) -> Any:
        """create"""
        _id = self.generate_id(data)
        d = copy.deepcopy(data)
        d["_id"] = _id
        self._datas[_id] = d
        return _id
