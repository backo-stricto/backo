"""Books module"""

# pylint: disable=unused-argument

from backo import (
    Dict,
    String,
    Collection,
    Item,
    log_system,
)
from backo.meta import NoneMetaDataHandler
from .db_country_connector import MyDBRestfullConnector

log = log_system.get_or_create_logger("countries")


# ------------------------------------------------
# ITEM
# ------------------------------------------------


# --------------------
# Description of "what is a country"
# --------------------
item = Item(
    {
        # "name": Dict({"common": String(), "official": String()}),
        "name": String(),
        "cca2": String(),
        "cca3": String(),
        "flags": Dict({"png": String(), "svg": String(), "alt": String()}),
    },
    meta_data_handler=NoneMetaDataHandler(),
)


# ------------------------------------------------
# COLLECTION
# ------------------------------------------------
connector = MyDBRestfullConnector()

countries = Collection(
    "countries",
    item,
    connector,
    can_create=False,
    can_modify=False,
    can_delete=False,
)


# ------------------------------------------------
# ACTIONS
# ------------------------------------------------

# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
