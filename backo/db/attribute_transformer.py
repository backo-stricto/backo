"""
module for transformers
"""
from abc import ABC, abstractmethod
from typing import Any
import re
import jsonpath


class AttributeTransformer(ABC):
    """
    Manage a transformarton
    """


    @abstractmethod
    def pre_write(self, path: str, _data: dict) -> dict:
        """
        return a patch operation to apply on the
        object BEFORE save(), create()...

        :return: a rfc6902 patch
        :rtype: dict
        """
        return None

    @abstractmethod
    def post_read(self, path: str, _data: dict) -> dict:
        """
        return a patch operation to apply on the
        object AFTER a load from the db

        :return: a rfc6902 patch
        :rtype: dict
        """
        return None


class RenameTransformer(AttributeTransformer):
    """
    Transformation to rename an attribute

    """
    def __init__(self, db_path: str):
        """
        :param db_path: The name of the attribute on the DB side
        :type db_path: str
        """
        self._db_path = db_path

        super().__init__()

    def pre_write(self, path: str, _data: dict) -> dict:
        """
        rename with a patch "move" operation
        """
        my_path_for_patch = re.sub(r"^\$\.|^@\.|\[|\]|\.", "/", self._db_path)
        path_for_patch = re.sub(r"^\$\.|^@\.|\[|\]|\.", "/", path)
        return {"op": "move", "from": path_for_patch, "path": my_path_for_patch}

    def post_read(self, path: str, _data: dict) -> dict:
        """
        rename with a patch "move" operation
        """
        my_path_for_patch = re.sub(r"^\$\.|^@\.|\[|\]|\.", "/", self._db_path)
        path_for_patch = re.sub(r"^\$\.|^@\.|\[|\]|\.", "/", path)
        return {"op": "move", "from": my_path_for_patch, "path": path_for_patch}


class IgnoreTransformer(AttributeTransformer):
    """
    Ignore transformation (drop a field)
    """

    def __init__(self, db_path: str):
        """
        :param db_path: The name of the attribute on the DB side
        :type db_path: str
        """
        self._db_path = db_path
        super().__init__()

    def pre_write(self, path: str, _data: dict) -> dict:
        """
        rename with a patch "move" operation
        """
        return None

    def post_read(self, path: str, _data: dict) -> dict:
        """
        rename with a patch "move" operation
        """
        my_path_for_patch = re.sub(r"^\$\.|^@\.|\[|\]|\.", "/", self._db_path)
        return {"op": "remove", "path": my_path_for_patch}


class ModifyTransformer(AttributeTransformer):
    """
    Modification (computation) transformer

    You can (re)define the value of an attribute
    withe the compute function

    """
    def __init__(self, db_path: str):
        """

        :param db_path: the 
        :type db_path: str
        """
        self._db_path = db_path

        super().__init__()

    @abstractmethod
    def compute(self, _data: dict) -> Any:
        """
        compute a valut to set to the object

        :param _data: the data loaded from the DB
        :type _data: dict
        :return: a value
        :rtype: Any
        """
        return None

    def pre_write(self, path: str, _data: dict) -> dict:
        """
        rename with a patch "move" operation
        """
        return None

    def post_read(self, path: str, _data: dict) -> dict:
        """
        rename with a patch "move" operation
        """
        path_for_patch = re.sub(r"^\$\.|^@\.|\[|\]|\.", "/", path)
        l = jsonpath.findall(path, _data)
        if len(l) == 1:
            return {
                "op": "replace",
                "path": path_for_patch,
                "value": self.compute(_data),
            }
        if len(l) == 0:
            return {"op": "add", "path": path_for_patch, "value": self.compute(_data)}

        raise KeyError(
            f'Cannot modify key "{path}" during post_read(). More than one key foundS'
        )
