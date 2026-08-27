# pylint: disable=relative-beyond-top-level
"""
Yaml connector as a directory
(each item is in one file)
"""

import uuid
import os
import copy
import re
import yaml
from stricto import SFilter
from .generic.db_handler import DBHandler
from .generic.interface import SelectResponse

from ..error import NotFoundError, DBError


class DBYmlDirConnector(DBHandler):
    """
    Yaml connector as a directory
    (each item is in one file)
    """

    def __init__(self, directory: str, **kwargs):
        """

        :param directory: the directory to store items
        :type directory: str
        :param item_handler: an ItemMapper, defaults to ItemMapper()
        :type item_handler: ItemMapper, optional
        :raises DBError: If the directory doesnt exist or is not writable
        """

        self._dir = directory

        if not os.path.exists(self._dir):
            os.makedirs(self._dir)

        if not os.path.isdir(self._dir):
            raise DBError('Yaml path "{0}" is not a directory', self._dir)

        super().__init__(directory, **kwargs)

    def connect(self) -> None:
        """No connection"""

    def close(self) -> None:
        """No close"""

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""
        dirs = os.listdir(self._dir)
        for file in dirs:
            if re.match(r".*\.yml$", file):
                os.unlink(os.path.join(self._dir, file))

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

    def get_by_id(self, _id: str) -> dict:
        """
        Get by id

        :param _id: the _id
        :type _id: str
        :raises NotFoundError: _description_
        :return: the object
        :rtype: dict
        """
        filename = os.path.join(self._dir, _id + ".yml")
        if not os.path.isfile(filename):
            raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

        with open(filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)

            # Do all transformations on the object
            self._transform_on_load(data_loaded)

            return data_loaded

        return None

    def delete_by_id(self, _id: str) -> None:
        """
        Delete

        :param _id: the _id of the objtct to delete
        :type _id: str
        :raises NotFoundError: if not found
        """
        filename = os.path.join(self._dir, _id + ".yml")
        if os.path.isfile(filename):
            os.remove(filename)
            return

        raise NotFoundError('_id "{0}" not found in "{1}"', _id, self._name)

    def create(self, o: dict) -> str:
        """
        Create an object

        :param o: The object
        :type o: dict
        :return: the If of the created object
        :rtype: str
        """
        _id = self.generate_id(o)
        d = copy.deepcopy(o)
        d["_id"] = _id

        # Do all transformations on the object
        self._transform_on_create(d)

        filename = os.path.join(self._dir, _id + ".yml")
        with open(filename, mode="w", encoding="utf-8") as outfile:
            yaml.dump(d, outfile, default_flow_style=False)

        return _id

    def save(self, _id: str, o: dict) -> None:
        """
        Save an existing object (update)

        :param _id: the _id of the object
        :type _id: str
        :param o: the object
        :type o: dict
        """
        filename = os.path.join(self._dir, _id + ".yml")

        # Do all transformations on the object
        self._transform_on_save(o)

        with open(filename, mode="w", encoding="utf-8") as outfile:
            yaml.dump(o, outfile, default_flow_style=False)

    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter,
        projection: list[str] = [],
        page_size=0,
        num_of_element_to_skip=0,
        sort_object: list[str] = [],
    ) -> SelectResponse:
        """
        Make a selection
        """

        response = SelectResponse(page_size, num_of_element_to_skip)

        try:
            dirs = os.listdir(self._dir)
            idx = 0
            for file in dirs:
                if not re.match(r".*\.yml$", file):
                    continue

                idx += 1
                # keep only elements in the windows [ num_of_element_to_skip, page_size + num_of_element_to_skip ]
                if idx < num_of_element_to_skip or (
                    num_of_element_to_skip
                    and idx > (page_size + num_of_element_to_skip)
                ):
                    continue

                with open(
                    os.path.join(self._dir, file), mode="r", encoding="utf-8"
                ) as stream:
                    data_loaded = yaml.safe_load(stream)

                # Do all transformations on the object
                self._transform_on_load(data_loaded)

                response.items.append(data_loaded)
                response.total = idx

        except Exception as e:
            raise DBError('Error while select in path "{0}"', self._dir) from e

        return response
