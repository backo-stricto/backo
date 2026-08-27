# pylint: disable=relative-beyond-top-level
"""
DB Connector redirect to another backo server
"""

from stricto import SFilter
from ..error import DBError
from .restfull import DBRestFullConnector
from .generic.interface import SelectResponse


class DBBackoRedirectConnector(
    DBRestFullConnector
):  # pylint: disable=too-many-instance-attributes
    """An example of a rest API connector"""

    _remote_collection: str = None

    def __init__(self, remote_collection: str, **kwargs):
        """constructor"""
        self._remote_collection = remote_collection
        DBRestFullConnector.__init__(self, f"redirect_{remote_collection}", **kwargs)

    def drop(self, **kwargs):  # pylint: disable=unused-argument
        raise DBError("DBRedirect doenst implement drop() method")

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        return self._internal_create(
            o,
            endpoint=self._remote_collection,
        )

    def save(self, _id: str, o: dict):
        return self._internal_save(
            _id,
            o,
            endpoint=self._remote_collection,
        )

    def delete_by_id(self, _id: str):
        return self._internal_delete_by_id(
            _id,
            endpoint=self._remote_collection,
        )

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""

        return self._internal_get_by_id(
            _id,
            endpoint=self._remote_collection,
        )

    def select(
        self,
        select_filter: SFilter,
        projection: list[str] = None,
        page_size=0,
        num_of_element_to_skip=0,
        sort_object: list[str] = [],
    ) -> SelectResponse:
        """See :func:`DBConnector.select`

        Params ``select_filter`` and ``projection`` are not used

        """
        return self._internal_select(
            select_filter,
            projection,
            page_size,
            num_of_element_to_skip,
            sort_object,
            endpoint=self._remote_collection,
        )
