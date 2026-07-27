# pylint: disable=too-few-public-methods
"""
Abstract class for Attribut Mapper
"""
from abc import ABC, abstractmethod
import sys

# used for developpement
sys.path.insert(1, "../../../stricto")


class AttributeMapper(ABC):
    """
    Manage a transformarton

    """

    @abstractmethod
    def get_for_projection(self, path: str) -> str:
        """
        return the attribut name when asked for the projection
        """
        return None

    @abstractmethod
    def get_for_filter(self, path: str) -> str:
        """
        return the attribut name when asked for the filter
        """
        return None
