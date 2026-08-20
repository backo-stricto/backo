"""
Attribut transformer
"""


class Transformer:
    """
    Transform attributes

    used to rewrite the path for filtering, projection...

    """

    def __init__(self, key_path: list[str], backo_type: str = None):
        self.key_path = key_path
        self.backo_type = backo_type

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

    def get_key_path(self) -> list[str]:
        """
        Return the key_path

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
