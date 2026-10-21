"""
Module providing the Meta_data_manipulation
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys

from .abstract_meta_handler import GenericMetaDataHandler

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Dict


class NoneMetaDataHandler(GenericMetaDataHandler):
    """
    A generic meta Data
    """

    def update(self, o: Dict) -> None:
        """
        No update
        """

    def append_schema(self, o: Dict) -> None:
        """
        No Scheme
        """
