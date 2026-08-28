"""
Module providing the Generic() Class for connection on DB
"""

# pylint: disable=relative-beyond-top-level
# (due to a pylint bug)

import uuid
import sys
from typing import Callable
from abc import ABC, abstractmethod

# used for developpement
sys.path.insert(1, "../../../stricto")

from stricto import Kparse, SFilter

from .transformer import Transformer
from .filter import Filter
from .interface import SelectResponse

from ...error import DBError

KPARSE_MODEL = {"restriction": Callable}


class DBHandler(ABC):  # pylint: disable=too-many-instance-attributes
    """Database Connector

    This is the way to save / store / retrieve objects


    """

    def __init__(self, db_name: str, **kwargs):
        """


        :param db_name: The name of the database (it is just a name)
        :type db_name: str
        """

        self._name = db_name
        self._table_name = None
        self.model = None
        self.filter: Filter = None
        self.transformers: dict[str, dict[str, Transformer]] = {}
        self.type_transformers: dict[str, Transformer] = {}

        options = Kparse(kwargs, KPARSE_MODEL)

        self.restriction_filter = options.get("restriction")

    def set_model(self, scheme: dict) -> None:
        """
        Register the model (backo meta() into the connector)

        :param scheme: backo meta data
        :type scheme: dict
        """
        self.model = scheme["item"]
        if self.filter:
            self.filter.set_model(scheme)

    def register_transformer(
        self, transformer: Transformer, table_name: str = None
    ) -> None:
        """
        Register a transformer

        :param transformer: the transformer to register
        :type transformer: Transformer
        :param table_name: The table_name, defaults to None
        :type table_name: str, optional
        """
        t_name = self._table_name if table_name is None else table_name

        if t_name not in self.transformers:
            self.transformers[t_name] = {}
        self.transformers[t_name]["_".join(transformer.key_path)] = transformer

    def register_type_transformer(self, transformer: Transformer) -> None:
        """
        Register a transformer for type (backo type, like String, Int...)

        :param transformer: the transformer
        :type transformer: Transformer
        """
        self.type_transformers[transformer.backo_type] = transformer

    def _transform_on_load(self, loaded_object: dict):
        for transformers in self.transformers.values():
            for transformer in transformers.values():
                try:
                    db_path = transformer.get_db_path()
                    if transformer.path_exists_in_object(db_path, loaded_object):
                        transformer.on_load(loaded_object, db_path)
                except Exception as e:
                    raise DBError("Transformer on load error") from e

    def _transform_on_create(self, obj: dict):
        for transformers in self.transformers.values():
            for transformer in transformers.values():
                try:
                    if transformer.path_exists_in_object(transformer.key_path, obj):
                        transformer.on_create(obj, transformer.key_path)
                except Exception as e:
                    raise DBError("Transformer on create error") from e

    def _transform_on_save(self, obj: dict):
        for transformers in self.transformers.values():
            for transformer in transformers.values():
                try:
                    if transformer.path_exists_in_object(transformer.key_path, obj):
                        transformer.on_save(obj, transformer.key_path)
                except Exception as e:
                    raise DBError("Transformer on save error") from e

    def get_transformer(
        self, key_path: list[str], table_name: str = None, backo_types: list[str] = None
    ) -> Transformer:
        """
        Get a transformer for this key_path and the table or type

        :param key_path: the key in the object (like [ 'address', 'street' ])
        :type key_path: list[str]
        :param table_name: the table_name, defaults to None
        :type table_name: str, optional
        :param backo_types: types of the key, defaults to None
        :type backo_types: list[str], optional
        :return: _description_A transformer or None
        :rtype: Transformer
        """

        if backo_types:
            for backo_type in backo_types:
                if backo_type in self.type_transformers:
                    return self.type_transformers[backo_type]

        t_name = self._table_name if table_name is None else table_name
        if t_name not in self.transformers:
            return None
        t_path = self.transformers[t_name]

        key = "_".join(key_path)
        if key not in t_path:
            return None
        return t_path[key]

    def check_structure(self, _update_directly=False) -> tuple[bool, str]:
        """

        Check if the internal structure is compliant to the model


        :param _update_directly: do the update automatically, defaults to False
        :type _update_directly: bool, optional
        :return: True if compliant, or False, and a message with things to do to be compliant
        :rtype: tuple [ bool, str ]
        """
        return (True, None)

    @abstractmethod
    def drop(self) -> None:  # pylint: disable=unused-argument
        """Drop the collection

        Mainly used in test


        :raise Error: Raise an error DBError or any db error
        """

    @abstractmethod
    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """

    @abstractmethod
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

    @abstractmethod
    def get_by_id(self, _id: str) -> dict:  # pylint: disable=unused-argument
        """
        get an object by _id in the DB and return it

        :param _id: the _id
        :type _id: str
        :return: The object (json format)
        :rtype: dict
        :raise Error: Raise an error DBError or any db error

        """

    @abstractmethod
    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        """Create the object into the DB and return the _id

        :param o: The object given (json format)
        :type o: dict
        :return: The _id of the object.
        :rtype: str


        :raise Error: Raise an error DBError or any db error

        """

    @abstractmethod
    def save(self, _id: str, o: dict) -> None:  # pylint: disable=unused-argument
        """Save the objet

        :param _id: the _id of this object
        :type _id: str

        :param o: The object given (json format)
        :type o: dict

        :raise Error: Raise an error DBError or any db error

        """

    @abstractmethod
    def delete_by_id(self, _id: str) -> None:
        """The _id to delete on the db

        :param _id: the _id
        :type _id: str
        :raise Error: Raise an error DBError or any db error
        """

    @abstractmethod
    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter,
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
