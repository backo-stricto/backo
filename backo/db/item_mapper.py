"""
Item mapper

"""

import sys
from typing import Any

from jsonpath import patch

# used for developpement
sys.path.insert(1, "../../../stricto")
from stricto import Kparse

from .attribute_mapper import AttributeMapper
from .attribute_transformer import AttributeTransformer

KPARSE_MODEL = {
    "default_attribute_mapper": AttributeMapper,
    "default_attribute_transformer": AttributeTransformer,
}


class ItemMapper:
    """
    Transform an item

    :param RequestResponse: _description_
    :type RequestResponse: _type_
    """

    def __init__(self, **kwargs):

        options = Kparse(kwargs, KPARSE_MODEL)

        self._attribute_mappers: dict[str, AttributeMapper] = {}
        self._type_mappers: dict[str, AttributeMapper] = {}

        self._attribute_transformers: dict[str, AttributeTransformer] = {}
        self._type_transformers: dict[str, AttributeTransformer] = {}

        self.default_attribute_mapper: AttributeMapper = options.get(
            "default_attribute_mapper"
        )
        self.default_attribute_transformer: AttributeTransformer = options.get(
            "default_attribute_transformer"
        )
        super().__init__()

    def add_attribute_mappers(
        self, attribute_name: str, mapper: AttributeMapper
    ) -> None:
        """
        _summary_

        :param path: _description_
        :type path: str
        :param mapper: _description_
        :type mapper: AttributHandler
        """
        self._attribute_mappers[attribute_name] = mapper

    def add_type_mappers(self, attribute_type: str, mapper: AttributeMapper) -> None:
        """
        _summary_

        :param path: _description_
        :type path: str
        :param mapper: _description_
        :type mapper: AttributHandler
        """
        self._type_mappers[attribute_type] = mapper

    def add_attribute_transformer(
        self, attribute_name: str, transformer: AttributeTransformer
    ) -> None:
        """
        _summary_

        :param path: _description_
        :type path: str
        :param mapper: _description_
        :type mapper: AttributHandler
        """
        self._attribute_transformers[attribute_name] = transformer

    def add_type_transformer(
        self, attribute_type: str, transformer: AttributeTransformer
    ) -> None:
        """
        _summary_

        :param path: _description_
        :type path: str
        :param mapper: _description_
        :type mapper: AttributHandler
        """
        self._type_transformers[attribute_type] = transformer

    def get_mapper(self, path: str, attr_type: str = None) -> AttributeMapper:
        """
        find the mapper, first by path, then by type, or the default

        :param path: exemple "$.name"
        :type path: str
        :param attr_type: example "String"
        :type attr_type: str
        :return: a mapper or None
        :rtype: AttributeMapper
        """
        if path:
            mapper = self._attribute_mappers.get(path)
            if mapper:
                return mapper
        if attr_type:
            return self._type_mappers.get(attr_type)
        return self.default_attribute_mapper

    def get_transformer(self, path: str, attr_type: str = None) -> AttributeTransformer:
        """
        find the transformer, first by path, then by type, or the default

        :param path: exemple "$.name"
        :type path: str
        :param attr_type: example "String"
        :type attr_type: str
        :return: a mapper or None
        :rtype: AttributeMapper
        """
        if path:
            mapper = self._attribute_transformers.get(path)
            if mapper:
                return mapper
        if attr_type:
            return self._type_transformers.get(attr_type)
        return self.default_attribute_transformer

    def do_pre_write(self, data: Any) -> None:
        """
        get data from the db and apply transformations

        :param data: _description_
        :type data: Any
        :return: _description_
        :rtype: Any
        """
        patch_operations = []
        for attribute_path, transformer in self._attribute_transformers.items():
            op = transformer.pre_write(attribute_path, data)
            if op:
                patch_operations.append(op)

        # can raise a JSONPatchError
        patch.atomic(patch_operations, data)

    def do_post_read(self, data: Any) -> None:
        """
        get data from the db and apply transformations

        :param data: _description_
        :type data: Any
        :return: _description_
        :rtype: Any
        """
        patch_operations = []
        for attribute_path, transformer in self._attribute_transformers.items():
            op = transformer.post_read(attribute_path, data)
            if op:
                patch_operations.append(op)

        # can raise a JSONPatchError
        patch.atomic(patch_operations, data)
