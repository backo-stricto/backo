# pylint: disable=relative-beyond-top-level
"""
Memory DB Connector
"""

import uuid
import copy
from stricto import SFilter
from .generic.db_handler import DBHandler
from .generic.interface import SelectResponse
from ..error import NotFoundError

from ..log import log_system

log = log_system.get_or_create_logger("DBMemoryConnector")


class DBMemoryConnector(DBHandler):
    """
    A memory storage (in a dict)
    """

    def __init__(self, db_name: str, **kwargs):
        """

        :param ``**kwargs``:
            See :py:class:`DBHandler`

        """

        self._datas: dict[str, dict] = {}

        super().__init__(db_name, **kwargs)

    def close(self) -> None:
        """nothing"""
        return

    def connect(self) -> None:
        """nothing"""
        return

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

    def get_by_id(self, _id: str) -> dict:
        """Get by id"""
        d = copy.deepcopy(self._datas.get(_id))
        if not d:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        # Do all transformations on the object
        self._transform_on_load(d)

        log.debug("Get {_id}")

        return d

    def delete_by_id(self, _id: str) -> None:
        """delete"""
        if _id not in self._datas:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        log.debug("Delete {_id}")

        del self._datas[_id]

    def save(self, _id: str, o: dict) -> None:
        """update one"""
        if _id not in self._datas:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        d = copy.deepcopy(o)
        d["_id"] = _id

        # Do all transformations on the object
        self._transform_on_save(d)

        log.debug("Save {_id}")

        self._datas[_id] = d

    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter = None,
        projection: list[str] = None,
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: list[str] = [],
    ) -> SelectResponse:
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
        response = SelectResponse(page_size, num_of_element_to_skip)
        response.total = len(self._datas.keys())
        for idx, d in enumerate(self._datas.values()):

            # keep only elements in the windows [ num_of_element_to_skip, page_size + num_of_element_to_skip ]
            if idx < num_of_element_to_skip or (
                num_of_element_to_skip and idx > (page_size + num_of_element_to_skip)
            ):
                continue

            # Do all transformations on the object
            self._transform_on_load(d)

            response.items.append(d)

        log.debug("Select return {response}")

        return response

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        """create"""
        _id = self.generate_id(o)
        d = copy.deepcopy(o)
        d["_id"] = _id

        # Do all transformations on the object
        self._transform_on_create(d)

        log.debug("Create {_id}")

        self._datas[_id] = d
        return _id
