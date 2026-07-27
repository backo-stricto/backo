# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""

from typing import Any
import re

from pymongo import MongoClient
from bson.objectid import ObjectId

from stricto import SFilter, Operator

from ..db_handler import DBHandler
from ..item_mapper import ItemMapper
from ..attribute_mapper import AttributeMapper
from ...error import NotFoundError, DBError
from ..request import (
    DeleteRequest,
    UpdateRequest,
    CreateRequest,
    SearchRequest,
    SelectRequest,
    Response,
)


class MongoAttributeMapper(AttributeMapper):
    """
    Attribut Mapper specific for Mongo

    ust to rewrite the path for filtering, projection...

    """

    def _path_to_mongo_path(self, path: str) -> str:
        """
        return the same path without "$."
        """
        return re.sub(r"^\$\.", "", path)

    def get_for_projection(self, path: str) -> str:
        """
        return the attribut name when asked for the projection
        """
        return self._path_to_mongo_path(path)

    def get_for_filter(self, path: str) -> str:
        """
        return the attribut name when asked for the filter
        """
        return self._path_to_mongo_path(path)


class MongoRenameMapper(MongoAttributeMapper):
    """
    A rename Mapper (to change the path of an attribut)
    """

    def __init__(self, db_path: str):
        """

        :param db_path: the name on the DB side
        :type db_path: str
        """
        self._db_path = db_path

        super().__init__()

    def get_for_projection(self, path: str) -> str:
        """
        return the attribut name when asked for the projection
        """
        return self._path_to_mongo_path(self._db_path)

    def get_for_filter(self, path: str) -> str:
        """
        return the attribut name when asked for the filter
        """
        return self._path_to_mongo_path(self._db_path)


class MongoItemMapper(ItemMapper):
    """
    Specific Mongo Item mapper
    (usee to transform SFilter to Mongo query)
    """

    def _sfilter_to_mongo_query(  # pylint: disable=too-many-return-statements, too-many-branches
        self, sf: SFilter
    ) -> dict:
        """

        Transform a SFilter to a mongo query

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """

        db_path = sf._path
        if db_path is not None:
            attribute_mapper = self.get_mapper(sf._path)
            if attribute_mapper:
                db_path = attribute_mapper.get_for_filter(sf._path)

        if sf._operator == Operator.AND:
            q = {}
            sub_list = []
            for sub in sf._value:
                sub_list.append(self._sfilter_to_mongo_query(sub))

            q["$and"] = sub_list
            return q

        if sf._operator == Operator.OR:
            q = {}
            sub_list = []
            for sub in sf._value:
                sub_list.append(self._sfilter_to_mongo_query(sub))

            q["$or"] = sub_list
            return q

        if sf._operator == Operator.NOT:
            q = {}
            q["$not"] = self._sfilter_to_mongo_query(sf._value)
            return q

        if sf._operator == Operator.EQ:
            q = {}
            q[db_path] = sf._value
            return q

        if sf._operator == Operator.GT:
            q = {}
            q[db_path] = {"$gt": sf._value}
            return q

        if sf._operator == Operator.GTE:
            q = {}
            q[db_path] = {"$gte": sf._value}
            return q

        if sf._operator == Operator.LTE:
            q = {}
            q[db_path] = {"$lte": sf._value}
            return q

        if sf._operator == Operator.LT:
            q = {}
            q[db_path] = {"$lt": sf._value}
            return q

        if sf._operator == Operator.NE:
            q = {}
            q[db_path] = {"$ne": sf._value}
            return q

        if sf._operator == Operator.REG:
            q = {}
            q[db_path] = {"$regex": sf._value}
            return q

        if sf._operator == Operator.SIZE:
            q = {}
            q[db_path] = {"$size": sf._value}
            return q

        # Not implemented
        return None


class MongoSelectRequest(SelectRequest):
    """
    The specific mongo selection Request
    """

    def __init__(
        self,
        sfilter: SFilter = None,
        projection: list[str] = [],
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
    ):
        """


        :param sfilter: the SFilter to transform to mongo filter, defaults to None
        :type sfilter: SFilter, optional
        :param projection: the projection, defaults to []
        :type projection: list[str], optional
        :param page_size: if pagination, the page size, defaults to 0
        :type page_size: int, optional
        :param num_of_element_to_skip: number of element to skip (for pagination), defaults to 0
        :type num_of_element_to_skip: int, optional
        :param sort_object: the sorting list, defaults to {"_id": 1}
        :type sort_object: dict, optional
        """

        self._page_size = page_size
        self._num_of_element_to_skip = num_of_element_to_skip
        self._sort_object = sort_object
        self._projection = projection

        super().__init__(sfilter, projection)


class DBMongoConnector(DBHandler):
    """
    DBConnector for mongoDB

    """

    def __init__(
        self,
        connection_string: str,
        collection: str,
        item_mapper: MongoItemMapper = MongoItemMapper(
            default_attribute_mapper=MongoAttributeMapper()
        ),
        **kwargs,
    ):
        """


        :param connection_string: the connection string to pass to MongoClient()
        :type connection_string: str
        :param collection: The name of the mongo collection
        :type collection: str
        :param item_mapper: a specific ItemMapper, defaults to MongoItemMapper( default_attribute_mapper=MongoAttributeMapper() )
        :type item_mapper: MongoItemMapper, optional
        """

        self._connection_string = connection_string
        self._collection_name = collection

        self._db = MongoClient(self._connection_string, **kwargs)

        self._database = self._db.get_default_database()
        self._collection = self._database[self._collection_name]

        super().__init__(collection, item_mapper, **kwargs)

        self.connect()

    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """
        try:
            return self._db.server_info()
        except Exception as e:
            raise DBError(
                'Mongo connection error at "{0}"', self._connection_string
            ) from e

    def close(self):
        """Close the mongodb connection

        :raise DBError: Raise an error in case of database Error

        """
        try:
            return self._db.close()
        except Exception as e:
            raise DBError('Mongo close error at "{0}"', self._connection_string) from e

    def drop(self) -> None:
        """
        Drop the entire collection

        """
        try:
            self._collection.drop()
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.drop()"', self._collection_name
            ) from e

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        """
        Not used in Mongo
        (the _id is generated by the DB itself)
        """
        raise DBError("Cannot use generate_id() in  DBMongoConnector")

    def db_build_search_request(self, request: SearchRequest) -> Any:
        """
        Build the Search request

        :param request: the request
        :type request: SearchRequest
        :return: a mongo query for this request
        :rtype: Any
        """
        return {"_id": ObjectId(request._id)}, request._id

    def db_search(self, search_request: tuple) -> Any:
        """get one"""
        mongo_filter, _id = search_request

        try:
            o = self._collection.find_one(mongo_filter)
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find_one()"', self._collection_name
            ) from e

        if o is None:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)
        o["_id"] = _id
        return o

    def db_build_delete_request(self, request: DeleteRequest) -> Any:
        """
        Build the Delete request

        :param request: the request
        :type request: DeleteRequest
        :return: a mongo query for this request
        :rtype: Any
        """
        return {"_id": ObjectId(request._id)}, request._id

    def db_delete(self, delete_request: tuple) -> Any:
        """delete"""
        mongo_filter, _id = delete_request

        try:
            result = self._collection.delete_one(mongo_filter)
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.delete_one()"', self._collection_name
            ) from e

        if result.deleted_count == 1:
            return True

        raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

    def db_build_update_request(self, request: UpdateRequest) -> Any:
        """
        Build the Update Request

        :param request: the request
        :type request: UpdateRequest
        :return: a mongo query for this request
        :rtype: Any
        """
        return {"_id": ObjectId(request._id)}, request._id, request._data

    def db_update(self, _id: str, update_request: tuple) -> Any:
        """update one"""
        mongo_filter, o, _id = update_request

        o["_id"] = ObjectId(_id)
        try:
            self._collection.find_one_and_replace(mongo_filter, o, {"upsert": True})
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find_one_and_replace()"',
                self._collection_name,
            ) from e

        return True

    def db_build_create_request(self, request: CreateRequest) -> Any:
        """
        Build the Update Create Request

        :param request: the request
        :type request: CreateRequest
        :return: the data
        :rtype: Any
        """
        return request._data

    def db_create(self, o: Any) -> Any:
        """create"""
        try:
            result = self._collection.insert_one(o)
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.insert_one()"', self._collection_name
            ) from e

        return str(result.inserted_id)

    def db_build_select_request(self, request: MongoSelectRequest) -> Any:
        """
        transform SFilter ( request._filter ) to mongodb filter

        :return: _description_
        :rtype: Any
        """
        return (
            self.item_mapper._sfilter_to_mongo_query(request._filter),
            request._projection,
            request._page_size,
            request._num_of_element_to_skip,
            request._sort_object,
        )

    def db_select(self, select_request: Any) -> Any:
        """select"""
        mongo_filter, projection, page_size, num_of_element_to_skip, sort_object = (
            select_request
        )

        print(f"select = { mongo_filter } {sort_object}")

        try:
            result_list = list(
                self._collection.find(mongo_filter, projection)
                .sort({"_id": 1})
                .skip(num_of_element_to_skip)
                .limit(page_size)
            )
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find()"', self._collection_name
            ) from e
        return result_list

    def select(
        self,
        select_filter: SFilter,
        projection: list[str] = [],
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: dict = None,
    ) -> Response:  # pylint: disable=unused-argument
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
        req = MongoSelectRequest(
            select_filter, projection, page_size, num_of_element_to_skip, sort_object
        )
        data = self.db_select(self.db_build_select_request(req))
        resp = Response()
        if self.item_mapper:
            if isinstance(data, list):
                for d in data:
                    self.item_mapper.do_post_read(d)

        resp.data = data
        return resp.data
