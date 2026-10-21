"""Users module"""

# pylint: disable=unused-argument

from backo import (
    String,
    Collection,
    Item,
    log_system,
    Ref,
    RefsList,
)
from backo.db import DBMongoConnector
from backo.meta import NoneMetaDataHandler

log = log_system.get_or_create_logger("user")


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
        "name": String(require=True, default=""),
        "surname": String(require=True, default=""),
        "first_nationality": Ref(coll="countries"),
        "other_nationalities": RefsList(coll="countries"),
    },
    meta_data_handler=NoneMetaDataHandler(),
)

# ------------------------------------------------
# COLLECTION
# ------------------------------------------------

# First define the connector  = where to store datas
connector = DBMongoConnector("mongodb://localhost:27017/country", "Users")


#
# The collection creation
#
# Association of Item, collector, rights
#
people = Collection(
    "people",
    item,
    connector,
)


# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
