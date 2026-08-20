# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""

from typing import Any, Callable
import re

from pymongo import MongoClient
from bson.objectid import ObjectId

from stricto import SFilter, Operator

from ..transformer import Transformer
from ..db_handler import DBHandler
from ...error import NotFoundError, DBError
from ..filter import Filter

class MongoFilter(Filter):

    def __init__(self, get_transformer: Callable ):
        super().__init__( get_transformer )


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

            db_path = re.sub(r"^\$\.", "", db_path)
            transformer:Transformer = self.get_transformer( [ db_path ] )
            if transformer:
                db_path = transformer.get_key_path()

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



    def build_db_filter(self, backo_filter: SFilter) -> Any:
        return self._sfilter_to_mongo_query( backo_filter )
        


class DBMongoConnector(DBHandler):
    """
    DBConnector for mongoDB

    """

    def __init__(
        self,
        connection_string: str,
        collection: str,
        **kwargs,
    ):
        """


        :param connection_string: the connection string to pass to MongoClient()
        :type connection_string: str
        :param collection: The name of the mongo collection
        :type collection: str
        :param item_mapper: a specific ItemMapper, defaults to MongoItemMapper( default_attribute_mapper=MongoAttributeMapper )
        :type item_mapper: MongoItemMapper, optional
        """

        self._connection_string = connection_string
        self._collection_name = collection

        self._db = MongoClient(self._connection_string, **kwargs)

        self._database = self._db.get_default_database()
        self._collection = self._database[self._collection_name]


        self.filter = MongoFilter( self.get_transformer )

        super().__init__(collection, **kwargs)

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
        raise DBError("Cannot use generate_id() in DBMongoConnector")



    def get_by_id(self, _id: str) -> dict:
        try:
            o = self._collection.find_one({ '_id' : ObjectId(_id) })
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find_one()"', self._collection_name
            ) from e

        if o is None:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)
        o["_id"] = _id
        return o


    def delete_by_id(self, _id: str)-> None:
        try:
            result = self._collection.delete_one({ '_id' : ObjectId(_id) })
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.delete_one()"', self._collection_name
            ) from e

        if result.deleted_count != 1:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

    def save(self, _id: str, o: dict)-> None:

        oid = ObjectId(_id)
        o["_id"] = oid
        try:
            self._collection.find_one_and_replace({ '_id' : oid }, o, {"upsert": True})
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find_one_and_replace()"',
                self._collection_name,
            ) from e



    def create(self, o: dict)-> str:

        try:
            result = self._collection.insert_one(o)
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.insert_one()"', self._collection_name
            ) from e

        return str(result.inserted_id)


    def select(
        self,
        select_filter: SFilter,
        projection: list[str] = [],
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: dict = None,
    ) -> list[ dict ]:  # pylint: disable=unused-argument
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


        mongo_filter = self.filter.build_db_filter(select_filter)
        
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

