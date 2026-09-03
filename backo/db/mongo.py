# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
db connector for Mongodb
"""

from typing import Any
import re
import copy
from datetime import datetime
from jsonpath import patch, findall

from pymongo import MongoClient
from bson.objectid import ObjectId

from stricto import SFilter, Operator

from .generic.transformer import Transformer
from .generic.db_handler import DBHandler
from .generic.interface import SelectResponse
from .generic.filter import Filter

from ..error import NotFoundError, DBError
from ..log import log_system

log = log_system.get_or_create_logger("DBMongoConnector")


class MongoFilter(Filter):
    """
    Filter transformation for mongo
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
        transformer: Transformer = None
        db_path_string = sf._path
        if db_path_string is not None:

            db_path_string = re.sub(r"^\$\.", "", db_path_string)
            db_path = db_path_string.split(".")
            transformer = self.get_transformer(db_path)
            if transformer:
                db_path = transformer.get_db_path(db_path)
                db_path_string = ".".join(db_path)

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

        db_value = (
            transformer.transform_value_to_db(sf._value) if transformer else sf._value
        )

        if sf._operator == Operator.EQ:
            q = {}
            q[db_path_string] = db_value
            return q

        if sf._operator == Operator.GT:
            q = {}
            q[db_path_string] = {"$gt": db_value}
            return q

        if sf._operator == Operator.GTE:
            q = {}
            q[db_path_string] = {"$gte": db_value}
            return q

        if sf._operator == Operator.LTE:
            q = {}
            q[db_path_string] = {"$lte": db_value}
            return q

        if sf._operator == Operator.LT:
            q = {}
            q[db_path_string] = {"$lt": db_value}
            return q

        if sf._operator == Operator.NE:
            q = {}
            q[db_path_string] = {"$ne": db_value}
            return q

        if sf._operator == Operator.REG:
            q = {}
            q[db_path_string] = {"$regex": db_value}
            return q

        if sf._operator == Operator.SIZE:
            q = {}
            q[db_path_string] = {"$size": db_value}
            return q

        # Not implemented
        return None

    def build_db_filter(self, backo_filter: SFilter) -> Any:
        """

        Transform a SFilter to a mongo query

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """
        if not backo_filter:
            return {}
        return self._sfilter_to_mongo_query(backo_filter)


class IdTransformer(Transformer):
    """
    specific transformer for _id
    (mongo use Object_id )
    """

    def __init__(self):
        super().__init__(["_id"])

    def on_load(self, _loaded_object: dict, _key_path: list[str]):
        """
        Change the id into _id and transform it from int to string

        :param _loaded_object: the object loaded
        :type _loaded_object: dict
        :param _key_path: Not used
        """
        _loaded_object["_id"] = str(_loaded_object["_id"])

    def on_create(self, obj: dict, _key_path: list[str]):
        """
        Delete the _id field if exists

        """
        del obj["_id"]


class DatetimeTransformer(Transformer):
    """
    specific transformer for Datetime
    (mongo use direct Date )
    """

    def __init__(self):
        super().__init__(None, "Datetime")

    def on_load(self, _loaded_object: dict, _db_path: list[str]):
        """
        Change the 0-1 into a bool value on load the object

        :param _loaded_object: The loaded dict
        :type _loaded_object: dict
        :param _key_path: the path of the bool in this _loaded_object
        :type _key_path: list[str ]
        """
        jpath = f"$.{'.'.join(_db_path)}"
        d = findall(jpath, _loaded_object)
        if d:
            value = self.transform_value_from_db(d[0])

            # print(f' load date {_db_path} = {type(value)} {value}')
            patch.apply(
                [{"op": "replace", "path": f'/{"/".join(_db_path)}', "value": value}],
                _loaded_object,
            )

            # Moving if necessary
            # TODO

    def transform_value_to_db(self, v: Any) -> Any:
        """
        Transform its value on save, create, filter

        """
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)

        return v

    def transform_value_from_db(self, v: Any) -> Any:
        """
        Transform its value on load

        """
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, str):
            return v
        return v

    def _on_save_create(self, obj: dict, _key_path: list[str]):
        jpath = f"$.{'.'.join(_key_path)}"
        d = findall(jpath, obj)
        if d:
            value = self.transform_value_to_db(d[0])

            # print(f' save/create date {_key_path} = {type(value)} {value}')
            patch.apply(
                [{"op": "replace", "path": f'/{"/".join(_key_path)}', "value": value}],
                obj,
            )

            # Moving if necessary
            db_path = self.get_db_path(_key_path)
            if db_path != _key_path:
                patch.apply(
                    [
                        {
                            "op": "move",
                            "from": f'/{"/".join(_key_path)}',
                            "path": f'/{"/".join(db_path)}',
                        }
                    ],
                    obj,
                )

    def on_create(self, obj: dict, _key_path: list[str]):
        """
        Delete the _id field if exists

        """
        return self._on_save_create(obj, _key_path)

    def on_save(self, obj: dict, _key_path: list[str]):
        """
        Save the _id field if exists

        """
        return self._on_save_create(obj, _key_path)


class DBMongoConnector(DBHandler):
    """
    DBConnector for mongoDB databases

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


        :param ``**kwargs``:
            See :py:class:`DBHandler`

        """

        self._connection_string = connection_string
        self._collection_name = collection

        self.mongo_kwargs = kwargs
        self._db = None

        super().__init__(collection, **kwargs)

        self.filter = MongoFilter(self.get_transformer_by_key)
        self.register_transformer(IdTransformer())
        self.register_type_transformer(DatetimeTransformer())
        self.connect()

    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """
        try:
            if not self._db:
                self._db = MongoClient(self._connection_string, **self.mongo_kwargs)
                self._database = self._db.get_default_database()
                self._collection = self._database[self._collection_name]

                # return self._db.server_info()
        except Exception as e:
            raise DBError(
                'Mongo connection error at "{0}"', self._connection_string
            ) from e

    def close(self):
        """Close the mongodb connection

        :raise DBError: Raise an error in case of database Error

        """
        try:
            if self._db:
                self._db.close()
                self._db = None
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
        return "666"

    def get_by_id(self, _id: str) -> dict:
        """get"""
        try:
            o = self._collection.find_one({"_id": ObjectId(_id)})
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find_one()"', self._collection_name
            ) from e

        if o is None:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)
        o["_id"] = _id

        # Do all transformations on the object
        self._transform_on_load(o)

        return o

    def delete_by_id(self, _id: str) -> None:
        """delete"""
        try:
            result = self._collection.delete_one({"_id": ObjectId(_id)})
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.delete_one()"', self._collection_name
            ) from e

        if result.deleted_count != 1:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

    def save(self, _id: str, o: dict) -> None:
        """save"""
        oid = ObjectId(_id)

        copied_object = copy.deepcopy(o)
        copied_object["_id"] = oid

        # Do all transformations on the object
        self._transform_on_save(copied_object)

        try:
            self._collection.find_one_and_replace(
                {"_id": oid}, copied_object, {"upsert": True}
            )
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find_one_and_replace()"',
                self._collection_name,
            ) from e

    def create(self, o: dict) -> str:
        """create"""

        if "_id" in o:
            del o["_id"]

        copied_object = copy.deepcopy(o)
        # Do all transformations on the object
        self._transform_on_create(copied_object)

        try:
            result = self._collection.insert_one(copied_object)
        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.insert_one()"', self._collection_name
            ) from e

        return str(result.inserted_id)

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

        mongo_filter = self.filter.build_db_filter(select_filter)
        mongo_projection = self.filter.build_db_projection(projection)

        response = SelectResponse(page_size, num_of_element_to_skip)

        try:
            result_list = list(
                self._collection.find(mongo_filter, mongo_projection)
                .sort({"_id": 1})
                .skip(num_of_element_to_skip)
                .limit(page_size)
            )
            if not page_size:
                response.total = len(result_list)

        except Exception as e:
            raise DBError(
                'Mongo connection error while "{0}.find()"', self._collection_name
            ) from e

        for o in result_list:
            # Do all transformations on the object
            self._transform_on_load(o)

            response.items.append(o)

        return response
