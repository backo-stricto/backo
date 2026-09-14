"""
test for DBConnectors
"""

# pylint: disable=too-many-statements, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import time
from datetime import datetime, timedelta
from backo import (
    ExpiredError,
    Item,
    String,
    Ref,
    Int,
    Dict,
    Float,
    List,
    Bool,
    Datetime,
    RefsList,
    DeleteStrategy,
    # log_system,
    # LogLevel,
)
from backo.db import DBMemoryConnector, CacheTransformer

FULL_USER = Item(
    {
        "name": String(),
        "surname": String(),
        "age": Int(),
        "date": Datetime(),
        "nicknames": List(String()),
        "nationalities": List(Dict({"country": String()})),
        "site": Ref(coll="sites", field="$.users"),
        "male": Bool(default=True),
    }
)

FULL_SITE = Item(
    {
        "name": String(required=True, default="Moon"),
        "address": String(),
        "weather": Dict({"sun": Float()}),
        "users": RefsList(
            coll="users",
            field="$.site",
            ods=DeleteStrategy.DELETE_REFERENCED_ITEMS,
        ),
    }
)

YML_DIR = "/tmp/backo_tests_connector"
YML_DIR_SITE = "/tmp/backo_tests_connector_site"
SQLITE3_DB = "/tmp/backo_tests_connector_sqlite3.db"
YML_FILE_DB = "/tmp/backo_yml_file_users.yml"
YML_FILE_DB_SITE = "/tmp/backo_yml_file_sites.yml"


NOW = datetime.now().replace(microsecond=0)


class TestDBConnectorCache(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        # log = log_system.get_or_create_logger("DBSqlite3Connector")
        # log.setLevel(LogLevel.DEBUG)
        self.connector = DBMemoryConnector("Memory")
        self.connector.register_transformer(CacheTransformer(timedelta(seconds=1)))

        super().__init__(*args, **kwargs)

    def setUp(self):
        self.connector.connect()
        self.connector.drop()
        return super().setUp()

    def test_create(self):
        """
        Test create
        """
        _id = self.connector.create({"name": "toto"})
        o = self.connector.get_by_id(_id)
        self.assertFalse("_expire" in o)
        time.sleep(1.5)
        with self.assertRaises(ExpiredError) as e:
            self.connector.get_by_id(_id)
        self.assertEqual(repr(e.exception), 'Exception("Object expired")')
