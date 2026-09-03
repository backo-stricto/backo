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

    This is the way to save / store / retrieve objects in different databases
    Eache Collection can be in a separate database. The connector is for each
    :py:class:`backo.Collection`

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

        self.transformers_per_db_path: dict[str, tuple[list[str], Transformer]] = {}
        self.transformers_per_key_path: dict[str, tuple[list[str], Transformer]] = {}

        self._temp_transformers: list[Transformer] = []
        self._temp_type_transformers: list[Transformer] = []

        options = Kparse(kwargs, KPARSE_MODEL)

        self.restriction_filter = options.get("restriction")

    def set_model(self, model: dict) -> None:
        """
        Register the model (backo meta() into the connector)

        :param model: Item model
        :type model: dict
        """
        self.model = model
        if self.filter:
            self.filter.set_model(model)

        # Re-arange transformer according to the model
        for transformer in self._temp_transformers:
            self._reorder_transformers_per_key(transformer)
        self._temp_transformers.clear()

        # Re-arange type transformer according to the model
        for transformer in self._temp_type_transformers:
            self._reorder_type_transformers_per_key(transformer, [], model)
        self._temp_type_transformers.clear()

    def _reorder_transformers_per_key(self, transformer: Transformer) -> None:
        # Add the transformer indexed by key_path
        key_path_string = None
        if transformer.key_path:
            key_path_string = "_".join(transformer.key_path)
        if key_path_string:
            self.transformers_per_key_path[key_path_string] = (
                transformer.key_path,
                transformer,
            )

        # Add the transformer indexed by db_path
        db_path_string = transformer.get_db_path()
        if db_path_string:
            self.transformers_per_db_path["_".join(db_path_string)] = (
                db_path_string,
                transformer,
            )

    def _reorder_type_transformers_per_key(
        self, transformer: Transformer, key_path: list[str], model: dict
    ) -> None:

        if key_path and transformer.backo_type in model["types"]:
            self.transformers_per_key_path["_".join(key_path)] = (key_path, transformer)
            db_path = transformer.get_db_path(key_path)
            if db_path:
                self.transformers_per_db_path["_".join(db_path)] = (
                    db_path,
                    transformer,
                )

        if "sub_scheme" in model:
            for k, v in model["sub_scheme"].items():
                new_key_path = key_path.copy()
                new_key_path.append(k)
                self._reorder_type_transformers_per_key(transformer, new_key_path, v)
            return

        # A list
        if "sub_type" in model:
            sub_model = model["sub_type"]
            new_key_path = key_path.copy()
            new_key_path.append("_")
            self._reorder_type_transformers_per_key(
                transformer, new_key_path, sub_model
            )
            return

    def register_transformer(self, transformer: Transformer) -> None:
        """
        Register a :py:class:`Transformer`

        :param transformer: the transformer to register
        :type transformer: :py:class:`Transformer`
        """
        # Already a model : store the transformer by key
        if self.model:
            self._reorder_transformers_per_key(transformer)
            return
        # Keep it temporary waiting for model to store transformer
        self._temp_transformers.append(transformer)

    def register_type_transformer(self, transformer: Transformer) -> None:
        """
        Register a :py:class:`Transformer` for type (backo type, like String, Int...)

        :param transformer: the transformer
        :type transformer: Transformer
        """

        if self.model:
            self._reorder_type_transformers_per_key(transformer, [], self.model)
            return
        # Keep it temporary waiting for model to store transformer
        self._temp_type_transformers.append(transformer)

    def _transform_on_load(self, loaded_object: dict):

        for db_path, transformer in self.transformers_per_db_path.values():
            if transformer.path_exists_in_object(db_path, loaded_object):
                try:
                    transformer.on_load(loaded_object, db_path)
                except Exception as e:
                    raise DBError("Transformer on load error") from e

    def _transform_on_create(self, obj: dict):

        for key_path, transformer in self.transformers_per_key_path.values():
            if transformer.path_exists_in_object(key_path, obj):
                try:
                    transformer.on_create(obj, key_path)
                except Exception as e:
                    raise DBError("Transformer on_create error") from e

    def _transform_on_save(self, obj: dict):

        for key_path, transformer in self.transformers_per_key_path.values():
            if transformer.path_exists_in_object(key_path, obj):
                try:
                    transformer.on_save(obj, key_path)
                except Exception as e:
                    raise DBError("Transformer on_save error") from e

    def get_transformer_by_key(
        self, key_path: list[str] = None, db_path: list[str] = None
    ) -> Transformer:
        """
        Get a transformer by key_path or by _db_path

        :param key_path: _description_, defaults to None
        :type key_path: list[str], optional
        :param db_path: _description_, defaults to None
        :type db_path: list[str], optional
        :return: _description_
        :rtype: Transformer
        """
        # print(f'get_trans_by_key {key_path} {db_path} {self.transformers_per_key_path}')
        if key_path:
            key_path_string = "_".join(key_path)
            if key_path_string in self.transformers_per_key_path:
                return self.transformers_per_key_path[key_path_string][1]
            return None
        if db_path:
            db_path_string = "_".join(db_path)
            if db_path_string in self.transformers_per_db_path:
                return self.transformers_per_db_path[db_path_string][1]

        return None

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
