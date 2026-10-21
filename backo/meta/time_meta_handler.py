"""
Module providing the Meta_data_manipulation
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
from .abstract_meta_handler import GenericMetaDataHandler

from datetime import datetime

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Dict, Datetime


class TimeMetaDataHandler(GenericMetaDataHandler):
    """
    A Meta data class handle _meta schema with

    * ctime : The creation time of the Item
    * mtime : The modification tome of the Item
    """

    def update(self, o: Dict) -> None:
        """
        Modification of metadata when the object will be created
        """
        permission_enabled = o._permissions.get_permissions_status()
        now = datetime.now()

        # Disable momentary permissions to change meta_data
        o.disable_permissions()

        # Set creation ctime and owner
        if o._meta.ctime == None:  # pylint: disable=singleton-comparison
            o._meta.ctime.set_value(now)

        # Set modificattion time
        o._meta.mtime.set_value(now)

        # Put permission back
        if permission_enabled is True:
            o.enable_permissions()

    def append_schema(self, o: Dict) -> None:
        """
        Add to the schema
        """
        o.add_to_model(
            "_meta",
            Dict(
                {
                    "ctime": Datetime(description="Creation time"),
                    "mtime": Datetime(description="Last modification time"),
                },
                can_modify=False,
                description="Meta data information",
            ),
        )
