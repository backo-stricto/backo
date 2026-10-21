"""Virtual Machines collection set."""

from constants import get_data_dir
from backo import (
    String,
    Collection,
    Item,
)
from backo.db import DBYmlDirConnector
from backo.meta import NoneMetaDataHandler

vms_store = DBYmlDirConnector(str(get_data_dir() / "vms"))

vms = Item(
    {"name": String(required=True), "image": String(required=True)},
    meta_data_handler=NoneMetaDataHandler(),
)

vms_coll = Collection("vms", vms, vms_store)
