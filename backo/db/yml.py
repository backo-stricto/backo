# pylint: disable=relative-beyond-top-level
"""
Yaml connector as a directory
(each item is in one file)
"""

import uuid
import os
import copy
import yaml
from jsonpath import pointer, patch

from stricto import Kparse, SFilter

from .generic.db_handler import DBHandler
from .generic.transformer import path_to_json_path
from .generic.interface import SelectResponse

from ..error import NotFoundError, DBError

from ..log import log_system

log = log_system.get_or_create_logger("DBYmlConnector")

KPARSE_MODEL = {
    "db_path": {"type": list[str], "default": []},
    "by_id": {"type": bool, "default": True},
}


class DBYmlConnector(DBHandler):
    """
    Yaml connector in a file
    (each item in the yaml file, in a sub element)
    """

    def __init__(self, filename: str, **kwargs):
        """

        :param filename: The yml file
        :type filename: str
        """
        self._filename = filename

        options = Kparse(kwargs, KPARSE_MODEL)

        # The path in the json struct to store datas
        self._db_path = options.get("db_path")

        # Store as a list or a dict ?
        self._by_id = options.get("by_id")

        super().__init__(filename, **kwargs)

    def check_structure(self, _update_directly=False) -> tuple[bool, str]:
        """
        Create the file of not exists, and create db_path if not.

        """
        message = ""
        some_changements = False

        if not os.path.isfile(self._filename) and not os.path.islink(self._filename):
            if _update_directly:
                data = {}
                dd = data
                for key in self._db_path:
                    dd[key] = {}
                    dd = dd[key]
                v = {} if self._by_id else []
                patch.apply(
                    [
                        {
                            "op": "add",
                            "path": path_to_json_path(self._db_path),
                            "value": v,
                        }
                    ],
                    data,
                )
                with open(self._filename, mode="w", encoding="utf-8") as stream:
                    yaml.safe_dump(data, stream, default_flow_style=False)
            else:
                message += f'You must create file "{self._filename}"'
                some_changements = True

        else:
            if _update_directly:
                with open(self._filename, mode="r+", encoding="utf-8") as stream:
                    data_loaded = yaml.safe_load(stream)

                    if not isinstance(data_loaded, dict) and self._db_path:
                        data_loaded = {}

                    dd = data_loaded
                    for key in self._db_path:
                        if not key in dd or not isinstance(dd[key], dict):
                            dd[key] = {}
                            dd = dd[key]

                    v = {} if self._by_id else []
                    patch.apply(
                        [
                            {
                                "op": "add",
                                "path": path_to_json_path(self._db_path),
                                "value": v,
                            }
                        ],
                        data_loaded,
                    )
                    stream.seek(0)
                    yaml.safe_dump(data_loaded, stream, default_flow_style=False)
                    stream.truncate()

        return (not some_changements, message)

    def connect(self) -> None:
        """
        A fake connection to the file

        :raises DBError: if the file is not available
        """
        try:
            f = open(  # pylint: disable=consider-using-with
                self._filename, mode="r", encoding="utf-8"
            )
            f.close() 
        except Exception as e:
            raise DBError('Yaml file error "{0}"', self._filename) from e


    def close(self) -> None:
        """No close"""

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""

        if self._db_path:
            if self._by_id:
                self._modify_dict(
                    {
                        "op": "replace",
                        "path": path_to_json_path(self._db_path),
                        "value": {},
                    }
                )
            else:
                self._modify_list(
                    {
                        "op": "replace",
                        "path": path_to_json_path(self._db_path),
                        "value": [],
                    }
                )
        else:
            data = {} if self._by_id else []
            with open(self._filename, mode="w", encoding="utf-8") as stream:
                yaml.dump(data, stream, default_flow_style=False)

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

    def _get_by_id(self, _id: str) -> tuple[dict, int]:
        with open(self._filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)

            db = pointer.resolve(self._db_path, data_loaded)
            if db is None:
                raise DBError(
                    'Path "{0}" dos not exist in database "{1}"',
                    ".".join(self._db_path),
                    self._name,
                )

            if self._by_id:
                if not isinstance(db, dict):
                    raise DBError(
                        'Database "{0}.{1}" must be a dict (and is {2})',
                        self._name,
                        ".".join(self._db_path),
                        type(db),
                    )
                if _id not in db:
                    return (None, -1)
                return (db[_id], _id)
            if not isinstance(db, list):
                raise DBError(
                    'Database "{0}.{1}" must be a list (and is {2})',
                    self._name,
                    ".".join(self._db_path),
                    type(db),
                )
            for idx, d in enumerate(db):
                if not isinstance(d, dict):
                    continue
                if "_id" in d and d["_id"] == _id:
                    return (d, idx)
            return (None, -1)

    def get_by_id(self, _id: str) -> dict:
        """
        Get by id

        :param _id: the _id
        :type _id: str
        :raises NotFoundError: _description_
        :return: the object
        :rtype: dict
        """
        o, _idx = self._get_by_id(_id)
        if o is None:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)
        o["_id"] = _id

        # Do all transformations on the object
        self._transform_on_load(o)

        return o

    def _modify_list(self, patch_operation: dict) -> bool:
        with open(self._filename, mode="r+", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)

            db = pointer.resolve(self._db_path, data_loaded)
            if db is None:
                raise DBError(
                    'Path "{0}" dos not exist in database "{1}"',
                    ".".join(self._db_path),
                    self._name,
                )

            if not isinstance(db, list):
                raise DBError(
                    'Database "{0}.{1}" must be a list (and is {2})',
                    self._name,
                    ".".join(self._db_path),
                    type(db),
                )

            patch.apply([patch_operation], data_loaded)
            stream.seek(0)
            yaml.safe_dump(data_loaded, stream, default_flow_style=False)
            stream.truncate()

    def _modify_dict(self, patch_operation: dict) -> bool:
        with open(self._filename, mode="r+", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)

            db = pointer.resolve(self._db_path, data_loaded)
            if db is None:
                raise DBError(
                    'Path "{0}" dos not exist in database "{1}"',
                    ".".join(self._db_path),
                    self._name,
                )

            if not isinstance(db, dict):
                raise DBError(
                    'Database "{0}.{1}" must be a dict (and is {2})',
                    self._name,
                    ".".join(self._db_path),
                    type(db),
                )

            patch.apply([patch_operation], data_loaded)
            stream.seek(0)
            yaml.safe_dump(data_loaded, stream, default_flow_style=False)
            stream.truncate()

    def delete_by_id(self, _id: str) -> None:
        """
        Delete

        :param _id: the _id of the objtct to delete
        :type _id: str
        :raises NotFoundError: if not found
        """
        obj, idx = self._get_by_id(_id)
        if obj is None:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        if self._by_id:
            p = self._db_path.copy()
            p.append(_id)
            self._modify_dict({"op": "remove", "path": path_to_json_path(p)})
        else:
            p = self._db_path.copy()
            p.append(str(idx))
            self._modify_list({"op": "remove", "path": path_to_json_path(p)})

    def create(self, o: dict) -> str:
        """
        Create an object

        :param o: The object
        :type o: dict
        :return: the If of the created object
        :rtype: str
        """
        _id = self.generate_id(o)
        copied_object = copy.deepcopy(o)

        obj, _idx = self._get_by_id(_id)
        if obj is not None:
            raise DBError('_id "{0}" already exists in "{1}"', _id, self._name)

        # Do all transformations on the object
        self._transform_on_create(copied_object)

        if self._by_id:
            p = self._db_path.copy()
            p.append(_id)
            self._modify_dict(
                {"op": "add", "path": path_to_json_path(p), "value": copied_object}
            )
        else:
            p = self._db_path.copy()
            p.append("-")
            copied_object["_id"] = _id
            self._modify_list(
                {"op": "add", "path": path_to_json_path(p), "value": copied_object}
            )

        return _id

    def save(self, _id: str, o: dict) -> None:
        """
        Save an existing object (update)

        :param _id: the _id of the object
        :type _id: str
        :param o: the object
        :type o: dict
        """
        obj, idx = self._get_by_id(_id)
        if obj is None:
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        copied_object = copy.deepcopy(o)

        # Do all transformations on the object
        self._transform_on_save(copied_object)

        if self._by_id:
            p = self._db_path.copy()
            p.append(_id)
            self._modify_dict(
                {"op": "replace", "path": path_to_json_path(p), "value": copied_object}
            )
        else:
            p = self._db_path.copy()
            p.append(str(idx))
            copied_object["_id"] = _id
            self._modify_list(
                {"op": "replace", "path": path_to_json_path(p), "value": copied_object}
            )

    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter,
        projection: list[str] = [],
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: list[str] = None,
    ) -> SelectResponse:
        """
        Make a selection
        """
        response = SelectResponse(page_size, num_of_element_to_skip)

        with open(self._filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)

            db = pointer.resolve(self._db_path, data_loaded)
            if db is None:
                raise DBError(
                    'Path "{0}" dos not exist in database "{1}"',
                    ".".join(self._db_path),
                    self._name,
                )
            if self._by_id:
                if not isinstance(db, dict):
                    raise DBError(
                        'Database "{0}.{1}" must be a dict (and is {2})',
                        self._name,
                        ".".join(self._db_path),
                        type(db),
                    )
                idx = 0
                for _id, o in db.items():
                    o[_id] = _id
                    idx += 1
                    # keep only elements in the windows [ num_of_element_to_skip, page_size + num_of_element_to_skip ]
                    if idx < num_of_element_to_skip or (
                        num_of_element_to_skip
                        and idx > (page_size + num_of_element_to_skip)
                    ):
                        continue

                    # Do all transformations on the object
                    self._transform_on_load(o)

                    response.items.append(o)
                response.total = idx
                return response

            if not isinstance(db, list):
                raise DBError(
                    'Database "{0}.{1}" must be a list (and is {2})',
                    self._name,
                    ".".join(self._db_path),
                    type(db),
                )
            # Do all transformations on the object
            for idx, o in enumerate(db):

                # keep only elements in the windows [ num_of_element_to_skip, page_size + num_of_element_to_skip ]
                if idx < num_of_element_to_skip or (
                    num_of_element_to_skip
                    and idx > (page_size + num_of_element_to_skip)
                ):
                    continue

                # Do all transformations on the object
                self._transform_on_load(o)

                response.items.append(o)

            response.total = idx
            return response
