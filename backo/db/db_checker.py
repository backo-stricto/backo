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
from .db_handler import DBHandler

KPARSE_MODEL = {"restriction": Callable}


class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class DBChecker(Singleton, ABC):  # pylint: disable=too-many-instance-attributes
    """Database integrity check beetween backo and the DB structure

    This is the way to save / store / retrieve objects

    :param ``**kwargs``:
        - *restriction=* ``func`` --
          not used yet


    """

    db_handler: DBHandler = None

    @abstractmethod
    def check_compliance(self, shema: dict) -> None:
        pass

    def set_db_handler(self, db_handler: DBHandler) -> None:
        self.db_handler = db_handler
