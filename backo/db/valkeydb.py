# pylint: disable=relative-beyond-top-level
"""
Valkey ( Redis ) DB Connector
"""

import uuid
import copy
import json
import redis
from stricto import SFilter
from .generic.db_handler import DBHandler
from .generic.interface import SelectResponse
from ..error import NotFoundError, DBError

from ..log import log_system

log = log_system.get_or_create_logger("DBKeyDB")

KPARSE_MODEL = {
    "host": {"type": str | None, "default": "localhost"},
    "port": {"type": int | None, "default": 6379},
    "db": {"type": int | None, "default": 0},
    "username": str,
    "password": str,
}


class DBValkeyConnector(DBHandler):
    """
    A memory storage for Valkey (redis)
    """

    def __init__(self, db_name: str, connection_url: str, **kwargs):
        """

        :param db_name: The name of the database (just a name)
        :type db_name: str
        :param connection_url: the redis url
        :type connection_url: str


        :param ``**kwargs``:
            See :py:class:`DBHandler`

        """
        self._connection_url = connection_url
        self._db = redis.Redis.from_url(
            self._connection_url, decode_responses=True, **kwargs
        )

        super().__init__(db_name, **kwargs)

    def close(self) -> None:
        """close"""
        try:
            self._db.close()
        except Exception as e:
            raise DBError('Error while close() in "{1}"', self._name) from e

    def connect(self) -> None:
        """check if up"""
        try:
            self._db.ping()
        except (redis.ConnectionError, redis.TimeoutError) as e:
            raise DBError('Error while connect() in "{1}"', self._name) from e

    def drop(self) -> None:
        """
        Drop all datas
        """
        try:
            self._db.flushdb()
        except Exception as e:
            raise DBError('Error while drop in "{1}"', self._name) from e

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

        try:
            d_as_string = self._db.get(_id)
        except Exception as e:
            raise DBError('Error while get {0} in "{1}"', _id, self._name) from e

        if not d_as_string:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        d = json.loads(d_as_string)
        d["_id"] = str(_id)
        # Do all transformations on the object
        self._transform_on_load(d)

        log.debug("Get {_id}")
        return d

    def delete_by_id(self, _id: str) -> None:
        """delete"""
        try:
            d_as_string = self._db.get(_id)
        except Exception as e:
            raise DBError('Error while Save {0} in "{1}"', _id, self._name) from e

        if not d_as_string:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        log.debug("Delete {_id}")
        self._db.delete(_id)

    def save(self, _id: str, o: dict) -> None:
        """update one"""

        try:
            d_as_string = self._db.get(_id)
        except Exception as e:
            raise DBError('Error while Save {0} in "{1}"', _id, self._name) from e

        if not d_as_string:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        # Do all transformations on the object
        d = copy.deepcopy(o)
        self._transform_on_save(d)

        log.debug("Save {_id}")
        self._db.set(_id, json.dumps(d))

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

        _ids = list(self._db.scan_iter("*"))
        response.total = len(_ids)

        pipe = self._db.pipeline()

        retrieved_ids = []
        for idx, _id in enumerate(_ids):
            # Get by page
            if idx < num_of_element_to_skip or (
                num_of_element_to_skip and idx > (page_size + num_of_element_to_skip)
            ):
                continue
            retrieved_ids.append(str(_id))
            pipe.get(_id)

        values_as_string = pipe.execute()

        for idx, _id in enumerate(retrieved_ids):

            d = json.loads(values_as_string[idx])
            d["_id"] = _id
            # Do all transformations on the object
            self._transform_on_load(d)

            response.items.append(d)

        log.debug(f"Select return {response}")

        return response

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        """create"""
        _id = self.generate_id(o)
        d = copy.deepcopy(o)
        if "_id" in d:
            del d["_id"]
        # Do all transformations on the object
        self._transform_on_create(d)

        log.debug("Create {_id} = {d}")
        self._db.set(_id, json.dumps(d))
        return _id
