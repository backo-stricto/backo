"""
Module using DBRestfullConnector to connect to the Hypervisor REST API

Note: we assume that the signature of some inherited methods differ from the mother class
"""

# pylint: disable=logging-fstring-interpolation,arguments-differ
from backo import (
    log_system,
    DBError,
)
from backo.db import DBRestFullConnector

log = log_system.get_or_create_logger("vms-connector")


class VMsConnector(DBRestFullConnector):  # pylint: disable=too-many-instance-attributes
    """An example of a rest API connector"""

    def __init__(self, **kwargs):
        """constructor"""
        DBRestFullConnector.__init__(
            self,
            "vms",
            host="localhost",
            port=12345,
            tls=False,
            prefix="api/v1/hypervisor",
            **kwargs,
        )

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        return o["_id"]

    def drop(self):  # pylint: disable=unused-argument
        raise DBError("VMsConnector doenst implement drop() method")

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        return self._internal_create(
            o,
            endpoint="vms",
        )

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        return self._internal_save(
            _id,
            o,
            endpoint="vms",
        )

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        return self._internal_delete_by_id(
            _id,
            endpoint="vms",
        )

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBHandler.get_by_id`"""
        return self._internal_get_by_id(
            _id,
            endpoint="vms",
        )

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
    ) -> list:
        """See :func:`DBHandler.select`

        Params ``select_filter`` and ``projection`` are not used

        """
        log.debug(
            "select(%r, %r).sort(%r).skip(%r).limit(%r)",
            select_filter,
            projection,
            sort_object,
            num_of_element_to_skip,
            page_size,
        )

        return self._internal_select(
            select_filter,
            projection,
            sort_object,
            num_of_element_to_skip,
            page_size,
            endpoint="vms",
            method="GET",
        )
