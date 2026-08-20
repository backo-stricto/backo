# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for sql db connector
"""

from ...transformer import Transformer


class BooleanTransformer(Transformer):
    """
    Transform a Boolean into 0 - 1 int for Sqlite3

    """

    def __init__(self):
        """ """
        super().__init__(None, "Bool")

    def on_load(self, _loaded_object: dict, _key_path: list[str]):
        """
        Change the 0-1 into a bool value on load the object

        :param _loaded_object: The loaded dict
        :type _loaded_object: dict
        :param _key_path: the path of the bool in this _loaded_object
        :type _key_path: list[str ]
        """
        db_path = "_".join(_key_path)
        _loaded_object[db_path] = bool(_loaded_object[db_path])


class IdTransformer(Transformer):
    """
    specific transformer for _id
    (Sqlite3 use int for _ids and backo use String )
    """

    def __init__(self):
        super().__init__(["_id"])

    def must_be_store_in_db(self):
        """
        _id as a field must be ignored into the DB (and use the build-in "id")

        :return: False
        :rtype: bool
        """
        return False

    def on_load(self, _loaded_object: dict, _key_path: list[str]):
        """
        Change the id into _id and transform it from int to string

        :param _loaded_object: the object loaded
        :type _loaded_object: dict
        :param _key_path: Not used
        """
        _loaded_object["_id"] = str(_loaded_object["id"])
        del _loaded_object["id"]

    def on_create(self, _obj: dict):
        """
        Delete the _id field if exists

        :param _obj: _description_
        :type _obj: dict
        """
        del _obj["_id"]

    def on_save(self, obj: dict):
        """
        Transform _id(string) into id(int)

        :param obj: _description_
        :type obj: dict
        """
        obj["id"] = int(obj["_id"])
        del obj["_id"]
