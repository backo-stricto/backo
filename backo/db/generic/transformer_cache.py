"""
Attribut transformer
"""

# pylint: disable=relative-beyond-top-level

from datetime import datetime, timedelta
from jsonpath import patch, findall
from .transformer import Transformer, path_to_json_path
from ...error import ExpiredError


class CacheTransformer(Transformer):
    """
    A transformer to manage cachin effect

    """

    def __init__(self, delay: timedelta = None, db_path: list[str] = ["_expire"]):
        """
        :param db_path: the path in the DB to ignore
        :type db_path: list[ str ]


        .. code-block:: python

            my_dbhandler.register_transformer(IgnoreTransformer(["address"]))
            # Will ignore $.address from the DB


        """
        self._delay = delay
        self.db_path = db_path
        super().__init__(db_path)

        self.key_path_string = path_to_json_path(self.key_path)
        self.db_path_string = path_to_json_path(self.db_path)

    def _on_write(self, obj: dict, _key_path: list[str]):
        """
        update t
        :param _loaded_object: the lodaded object
        :type _loaded_object: dict
        :param _key_path: a key path as list
        :type _key_path: list[str]
        """
        expire = datetime.timestamp(datetime.now() + self._delay)

        patch.apply(
            [{"op": "add", "path": self.db_path_string, "value": expire}],
            obj,
        )

    def path_exists_in_object(self, _searching_path, _obj):
        """see parent"""
        return True

    def on_create(self, _obj: dict, _key_path: list[str]):
        """On creation modification"""
        print("on create")
        return self._on_write(_obj, _key_path)

    def on_save(self, obj: dict, _key_path: list[str]):
        """On save modification"""
        print("on save")
        return self._on_write(obj, _key_path)

    def on_load(self, loaded_object: dict, _key_path: list[str]):
        """
        Called when the object is read from the DB.
        Drop cache attribute
        """

        now = datetime.timestamp(datetime.now())

        jpath = f"$.{'.'.join(self.db_path)}"
        d = findall(jpath, loaded_object)
        if d:
            print("on load")
            if now > d[0]:
                raise ExpiredError("Object expired")

        patch.apply([{"op": "remove", "path": self.db_path_string}], loaded_object)

    def get_db_path(self, _key_path: list[str] = None) -> list[str]:
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
