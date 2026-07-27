# pylint: disable=relative-beyond-top-level
"""
Yaml connector as a directory
(each item is in one file)
"""

import uuid
from typing import Any
import os
import copy
import re
import yaml
from ..db_handler import DBHandler
from ..item_mapper import ItemMapper
from ...error import NotFoundError, DBError
from ..request import (
    DeleteRequest,
    UpdateRequest,
    CreateRequest,
    SearchRequest,
    SelectRequest,
)


class DBYmlDirConnector(DBHandler):
    """
    Yaml connector as a directory
    (each item is in one file)
    """

    def __init__(
        self, directory: str, item_handler: ItemMapper = ItemMapper(), **kwargs
    ):
        """

        :param directory: the directory to store items
        :type directory: str
        :param item_handler: an ItemMapper, defaults to ItemMapper()
        :type item_handler: ItemMapper, optional
        :raises DBError: If the directory doesnt exist or is not writable
        """

        self._dir = directory

        if not os.path.exists(self._dir):
            os.makedirs(self._dir)

        if not os.path.isdir(self._dir):
            raise DBError('Yaml path "{0}" is not a directory', self._dir)

        super().__init__(directory, item_handler, **kwargs)

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""
        dirs = os.listdir(self._dir)
        for file in dirs:
            if re.match(r".*\.yml$", file):
                os.unlink(os.path.join(self._dir, file))

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

        filename = os.path.join(self._dir, _id + ".yml")
        if not os.path.isfile(filename):
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        with open(filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)
            return data_loaded

        return None

    def db_build_delete_request(self, request: DeleteRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: SearchRequest
        :return: the understandable version of the request for thos connector
        :rtype: Any
        """
        return request._id

    def db_delete(self, _id: str) -> Any:
        """delete"""
        filename = os.path.join(self._dir, _id + ".yml")
        if os.path.isfile(filename):
            os.remove(filename)
            return True

        raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

    def db_build_create_request(self, request: CreateRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: SearchRequest
        :return: the understandable version of the request for thos connector
        :rtype: Any
        """
        return request._data

    def db_create(self, data) -> Any:
        """update one"""
        _id = self.generate_id(data)
        d = copy.deepcopy(data)
        d["_id"] = _id

        filename = os.path.join(self._dir, _id + ".yml")
        with open(filename, mode="w", encoding="utf-8") as outfile:
            yaml.dump(d, outfile, default_flow_style=False)

        return _id

    def db_build_update_request(self, request: UpdateRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: SearchRequest
        :return: the understandable version of the request for thos connector
        :rtype: Any
        """
        return request._id, request._data

    def db_update(self, _id, data) -> Any:
        """update one"""
        filename = os.path.join(self._dir, _id + ".yml")

        with open(filename, mode="w", encoding="utf-8") as outfile:
            yaml.dump(data, outfile, default_flow_style=False)

    def db_build_select_request(self, request: SelectRequest) -> Any:
        """
        build the request

        :param request: the request
        :type request: SearchRequest
        :return: the understandable version of the request for thos connector
        :rtype: Any
        """
        return request._filter, request._projection

    def db_select(  # pylint: disable=unused-argument
        self, db_request: SelectRequest
    ) -> Any:
        """select"""

        try:
            result_list = []
            dirs = os.listdir(self._dir)
            for file in dirs:
                if not re.match(r".*\.yml$", file):
                    continue

                with open(
                    os.path.join(self._dir, file), mode="r", encoding="utf-8"
                ) as stream:
                    data_loaded = yaml.safe_load(stream)
                result_list.append(data_loaded)
        except Exception as e:
            raise DBError('Error while select in path "{0}"', self._dir) from e

        return result_list
