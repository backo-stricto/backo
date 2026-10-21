"""
Module providing the Meta_data_manipulation
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
from abc import ABC, abstractmethod

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Dict


class GenericMetaDataHandler(ABC):  # pylint: disable=too-many-instance-attributes
    """
    A generic meta Data
    """

    def __init__(self):
        """
        Nothing to do
        """

    @abstractmethod
    def update(self, o: Dict) -> None:
        """
        Modification of metadata when the object will be created
        """

    @abstractmethod
    def append_schema(self, o: Dict) -> None:
        """
        Add to the schema
        """
