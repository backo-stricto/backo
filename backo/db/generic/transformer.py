"""
Attribut transformer
"""

import uuid

from jsonpath import patch, findall


def path_to_json_path(p: list[str]) -> str:
    """
    Transform the list path into a string wuth '/' as separators

    :param p: list of path
    :type p: list[str]
    :return: the /foo/bar
    :rtype: str
    """
    if p is None:
        return None
    return "/" + "/".join(p)


class Transformer:
    """
    Transform attributes

    used to make some transformations on the object before save into the DB, after load, ignore
    element, etc.

    """

    def __init__(self, key_path: list[str], backo_type: str = None):
        """


        :param key_path: path as list (like ['address', 'street']) on the backo side
        :type key_path: list[str]
        :param backo_type: If this transformer is "attached" to a type (like Int, Ref, Float...) rather than a key_path, defaults to None
        :type backo_type: str, optional
        """
        self.key_path = key_path
        self.backo_type = backo_type

    def path_exists_in_object(self, searching_path: list[str], obj: dict) -> bool:
        """
        Check if the path given exists in the object.

        :param searching_path: a path like [ 'address', 'street' ]
        :type searching_path: list[str]
        :param obj: the dict in which we search
        :type obj: dict
        :return: True if exist or False
        :rtype: bool
        """
        if searching_path is None:
            return False
        jpath = f"$.{'.'.join(searching_path)}"
        return bool(findall(jpath, obj))

    def on_load(self, _loaded_object: dict, _key_path: list[str]):
        """
        Called when the object is read from the DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        return

    def on_create(self, _obj: dict, _key_path: list[str]):
        """
        Called when the object is created, just before inserting in DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        return

    def on_save(self, _obj: dict, _key_path: list[str]):
        """
        Called when the object is saved, just before save in DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        return

    def get_db_path(self) -> list[str]:
        """
        Return the db_path (by default = sekf.key_path )

        :return: the key path associated to this transformer
        :rtype: list[str]
        """
        return self.key_path

    def must_be_store_in_db(self) -> bool:
        """
        Return if this key path must be saved into the DB.

        :return: True if must be saved,
        :rtype: bool
        """
        return True


class RenameTransformer(Transformer):
    """
    A transformer to rename a path into another.
    Usage :

    .. code-block:: python

        mydb_handler.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        # Will rename $.age into $.age_in_db, for everything (filtering, etc...)



    """

    def __init__(self, key_path: list[str], db_path: list[str], backo_type: str = None):
        """

        :param key_path: the path in backo, like [ 'address', 'street' ]
        :type key_path: list[ str ]
        :param db_path: _description_
        :type db_path: list[ str ]
        :param backo_type: _description_, defaults to None
        :type backo_type: str, optional
        """
        self.db_path = db_path
        super().__init__(key_path, backo_type)

        self.key_path_string = path_to_json_path(self.key_path)
        self.db_path_string = path_to_json_path(self.db_path)

    def on_load(self, loaded_object: dict, _key_path: list[str]):
        """
        Called when the object is read from the DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        patch.apply(
            [{"op": "move", "from": self.db_path_string, "path": self.key_path_string}],
            loaded_object,
        )

    def on_create(self, obj: dict, _key_path: list[str]):
        """
        Called when the object is created, just before inserting in DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        patch.apply(
            [{"op": "move", "from": self.key_path_string, "path": self.db_path_string}],
            obj,
        )

    def on_save(self, obj: dict, _key_path: list[str]):
        """
        Called when the object is saved, just before save in DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        patch.apply(
            [{"op": "move", "from": self.key_path_string, "path": self.db_path_string}],
            obj,
        )

    def get_db_path(self) -> list[str]:
        """
        Return the key_path

        :return: the key path associated to this transformer
        :rtype: list[str]
        """
        return self.db_path


class IgnoreTransformer(Transformer):
    """
    A transformer to ignore some elements in the DB

    """

    def __init__(self, db_path: list[str]):
        """
        :param db_path: the path in the DB to ignore
        :type db_path: list[ str ]


        .. code-block:: python

            my_dbhandler.register_transformer(IgnoreTransformer(["address"]))
            # Will ignore $.address from the DB


        """
        fake_key_path = ["_" + str(uuid.uuid4().int >> 64)]
        self.db_path = db_path
        super().__init__(fake_key_path)

        self.key_path_string = path_to_json_path(self.key_path)
        self.db_path_string = path_to_json_path(self.db_path)

    def on_load(self, loaded_object: dict, _key_path: list[str]):
        """
        Called when the object is read from the DB.
        You can do some changement into the object (delete keys, modifications, ...)

        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        patch.apply([{"op": "remove", "path": self.db_path_string}], loaded_object)

    def get_db_path(self) -> list[str]:
        """
        Return the key_path

        :return: the key path associated to this transformer
        :rtype: list[str]
        """
        return self.db_path

    def must_be_store_in_db(self) -> bool:
        """
        Return if this key path must be saved into the DB.

        :return: True if must be saved,
        :rtype: bool
        """
        return True
