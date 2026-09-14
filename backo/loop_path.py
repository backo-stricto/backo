"""
Loop path manipulation
"""

from .error import BackoError

DEFAULT_MAX_LOOP = 4

from .log import log_system

log = log_system.get_or_create_logger("ref")


class LoopPath:
    """
    A loop object to detect loop maniipulation in reference
    """

    def __init__(self, max_loop=DEFAULT_MAX_LOOP):
        """ """
        self._path = []
        self.max_loop = max_loop

    def is_loop(self, collection_name: str, _id: str, path: str) -> bool:
        """detect if already in the path

        :param collection_name: the name of the collection
        :type collection_name: str
        :param _id: the _id of the object in the collection
        :type _id: str
        :param path: the path (ex : $.site )
        :type path: str
        :return: True if seen
        :rtype: bool
        """
        for m_path in self._path:
            if m_path == (collection_name, _id, path):
                return True
        return False

    def append_or_loop(self, collection_name: str, _id: str, path: str) -> bool:
        """Append to the path a tuple (collection, _id, path )

        :param collection_name: the name of the collection
        :type collection_name: str
        :param _id: the _id of the object in the collection
        :type _id: str
        :param path: the path (ex : $.site )
        :type path: str
        """

        if len(self._path) > self.max_loop:
            raise BackoError(
                "Loop max detected for ( {0}, {1}, {2})", collection_name, _id, path
            )

        if self.is_loop(collection_name, _id, path):
            log.debug(
                f"Looper {id(self)} Loop detected {(collection_name, _id, path)} len={len(self._path)}"
            )
            return True

        self._path.append((collection_name, _id, path))
        return False
