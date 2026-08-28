"""Users module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from constants import get_data_dir
from backo import (
    String,
    Collection,
    Item,
    GenericMetaDataHandler,
    log_system,
    RefsList,
)
from backo.db import DBYmlDirConnector

log = log_system.get_or_create_logger("users")


# ------------------------------------------------
# ITEM
# ------------------------------------------------


# ------------------------------------
# Description of the Item
#
# The item is the object in the collection
# ------------------------------------
item = Item(
    {
        "name": String(require=True),
        "surname": String(require=True),
        "login": String(require=True),
        "vms": RefsList(coll="vms"),
    },
    meta_data_handler=GenericMetaDataHandler(),
)

# ------------------------------------------------
# COLLECTION
# ------------------------------------------------

# First define the connector  = where to store datas
connector = DBYmlDirConnector(str(get_data_dir() / "users"))


#
# The collection creation
#
# Association of Item, collector, rights
#
users = Collection(
    "users",
    item,
    connector,
)


# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
