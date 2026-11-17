"""
test for DBConnectors
"""

# pylint: disable=too-many-statements, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest

# from datetime import datetime, timedelta
from backo import (
    NotFoundError,
    Item,
    String,
    Ref,
    Int,
    Dict,
    List,
    Bool,
    Datetime,
    SFilter,
    Operator,
)
from backo.db import (
    DBMemoryConnector,
    DBExtenderConnector,
    DBYmlDirConnector,
    SelectResponse,
    DBMongoConnector,
    DBValkeyConnector,
    DBYmlConnector,
    DBSqlite3Connector,
    DBPostgresConnector,
)

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


YML_DIR_REMOTE = "/tmp/backo_tests_mix_remote"
YML_DIR_LOCAL = "/tmp/backo_tests_mix_local"
SQLITE3_DB = "/tmp/backo_tests_connector_sqlite3.db"
YML_FILE_REMOTE_DB = "/tmp/backo_yml_file_remote.yml"
YML_FILE_LOCAL_DB = "/tmp/backo_yml_file_local.yml"
POSTGRESS = "postgresql://test:test@localhost:5432/test_db"

ALL_REMOTE_CONNECTOR = [
    ("Redis", DBValkeyConnector("Redis", "redis://localhost:6379/0")),
    (YML_DIR_REMOTE, DBYmlDirConnector(YML_DIR_REMOTE)),
    (YML_FILE_REMOTE_DB, DBYmlConnector(YML_FILE_REMOTE_DB)),
    (
        YML_FILE_REMOTE_DB,
        DBYmlConnector(YML_FILE_REMOTE_DB, by_id=False, db_path=["home", "sub2"]),
    ),
    (YML_FILE_REMOTE_DB, DBYmlConnector(YML_FILE_REMOTE_DB, db_path=["home", "sub"])),
    ("mongo", DBMongoConnector("mongodb://localhost:27017/testMongo", "remote")),
    (SQLITE3_DB, DBSqlite3Connector(SQLITE3_DB, "remote")),
    ("postgress", DBPostgresConnector(POSTGRESS, "remote")),
]
ALL_LOCAL_CONNECTOR = [
    ("Memory", DBMemoryConnector("Memory")),
    ("Redis", DBValkeyConnector("Redis", "redis://localhost:6379/1")),
    (YML_DIR_LOCAL, DBYmlDirConnector(YML_DIR_LOCAL)),
    (YML_FILE_LOCAL_DB, DBYmlConnector(YML_FILE_LOCAL_DB)),
    (
        YML_FILE_LOCAL_DB,
        DBYmlConnector(YML_FILE_LOCAL_DB, by_id=False, db_path=["home", "sub2"]),
    ),
    (YML_FILE_LOCAL_DB, DBYmlConnector(YML_FILE_LOCAL_DB, db_path=["home", "sub"])),
    ("mongo", DBMongoConnector("mongodb://localhost:27017/testMongo", "local")),
    (SQLITE3_DB, DBSqlite3Connector(SQLITE3_DB, "local")),
    ("postgress", DBPostgresConnector(POSTGRESS, "local")),
]

CONNECTOR_REMOTE = ALL_REMOTE_CONNECTOR[0:7]
CONNECTOR_LOCAL = ALL_LOCAL_CONNECTOR[0:8]


class TestDBExtenderConnector(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """

        # log_system.add_handler(log_system.set_streamhandler())
        # log = log_system.get_or_create_logger("DBSqlite3Connector")
        # log.setLevel(LogLevel.DEBUG)
        # log = log_system.get_or_create_logger("DBMultiplexconnector")
        # log.setLevel(LogLevel.DEBUG)

        super().__init__(*args, **kwargs)

    def sub_test_init_connector(self, con: DBExtenderConnector):
        """
        test Initialisation for every DBHandler

        """
        con.set_model(FULL_USER)
        con.connect()

        # Built the structure
        con.check_structure(True)

        # check the structure
        rep, _mess = con.check_structure()

        self.assertEqual(rep, True)

        # Drop
        con.drop()

    def sub_test_create(self, con: DBExtenderConnector) -> str:
        """
        test creation

        """
        _id = con.create(
            {"name": "toto", "age": 22, "surname": "titi", "nicknames": ["to", "ti"]}
        )
        self.assertIsNotNone(_id)
        o = con.get_by_id(_id)
        self.assertEqual(o.get("name"), "toto")
        return _id, o

    def sub_test_update(self, con: DBExtenderConnector, _id: str) -> None:
        """
        test update

        """
        o = con.get_by_id(_id)
        self.assertIsNotNone(o)

        # update
        o["name"] = "toto_new"
        o["surname"] = "titi_new"
        o["nicknames"] = ["tonew", "tinew"]
        con.save(_id, o)

        o = con.get_by_id(_id)
        self.assertEqual(o.get("name"), "toto_new")

    def sub_test_select(self, con: DBExtenderConnector) -> None:
        """
        test select

        """
        max_item = 10

        con._origin_db_handler.drop()
        con._replicate_db_handler.drop()

        # Insert into the database
        for i in range(0, max_item):
            if i < 5:
                con._origin_db_handler.create({"name": f"rambo_{i}", "age": i})
                continue
            _id = con.create(
                {
                    "name": f"rambo_{i}",
                    "surname": f"Mickey_{i}",
                    "age": i,
                    "nicknames": [f"john_{i}", f"jojo_{i}"],
                }
            )
            self.assertIsNotNone(_id)

        # Select One
        res = con.select(SFilter("$.name", Operator.EQ, "rambo_1"))
        self.assertEqual(type(res), SelectResponse)
        if res.more_than_filter is False:
            self.assertEqual(len(res.items), 1)
        else:
            self.assertGreaterEqual(len(res.items), 1)

        # Select All
        res = con.select(None)
        self.assertEqual(type(res), SelectResponse)
        self.assertEqual(len(res.items), max_item)

    def _check_keys(
        self,
        con: DBExtenderConnector,
        _id: str,
        local_keys: dict,
        remote_keys: dict = None,
    ):
        local_obj = con._replicate_db_handler.get_by_id(_id)
        for key, value in local_keys.items():
            if value is None:
                self.assertIsNone(local_obj.get(key))
                continue

            self.assertEqual(local_obj.get(key), value)

        if not remote_keys:
            self.assertIsNone(local_obj.get("_origin_id"))
            return

        self.assertIsNotNone(local_obj.get("_origin_id"))
        o = con._origin_db_handler.get_by_id(local_obj.get("_origin_id"))
        self.assertIsNotNone(o)
        for key, value in remote_keys.items():
            if value is None:
                self.assertIsNone(o.get(key))
                continue

            self.assertEqual(o.get(key), value)

    def sub_test_delete(self, con: DBExtenderConnector, _id: str) -> str:
        """
        test delete

        """
        local_obj = con._replicate_db_handler.get_by_id(_id)
        con.delete_by_id(_id)
        with self.assertRaises(NotFoundError) as e:
            con.get_by_id(_id)
        self.assertIn(f'_id "{_id}" not found in', e.exception.to_string())

        return local_obj.get("_origin_id")

    def test_local_copy_noexpire_noupdate(self):
        """
        Test with local variables, copy, and no expire
        """

        for remote in CONNECTOR_REMOTE:
            for local in CONNECTOR_LOCAL:

                print(f"test with {remote[0]} -> {local[0]}")

                con = DBExtenderConnector(
                    "mix",
                    remote[1],
                    local[1],
                    local=["$.surname", "$.nicknames"],
                    replicate_origin=True,
                    sync_origin=False,
                )
                with self.subTest(con=con):
                    self.sub_test_init_connector(con)
                    _id, _obj = self.sub_test_create(con)
                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": "toto",
                            "age": 22,
                            "surname": "titi",
                            "nicknames": ["to", "ti"],
                        },
                    )
                    self.sub_test_update(con, _id)
                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": "toto_new",
                            "age": 22,
                            "surname": "titi_new",
                            "nicknames": ["tonew", "tinew"],
                        },
                    )
                    self.sub_test_delete(con, _id)
                    self.sub_test_select(con)

    def test_create_local_nocopy_noexpire_update(self):
        """
        Test with local variables, no copy, and no expire
        """

        for remote in CONNECTOR_REMOTE:
            for local in CONNECTOR_LOCAL:

                print(f"test with {remote[0]} -> {local[0]}")

                con = DBExtenderConnector(
                    "mix",
                    remote[1],
                    local[1],
                    local=["$.surname", "$.nicknames"],
                    replicate_origin=False,
                    sync_origin=True,
                )
                with self.subTest(con=con):
                    self.sub_test_init_connector(con)
                    _id, _obj = self.sub_test_create(con)

                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": None,
                            "age": None,
                            "surname": "titi",
                            "nicknames": ["to", "ti"],
                        },
                        {"name": "toto", "age": 22, "surname": None, "nicknames": None},
                    )

                    self.sub_test_update(con, _id)
                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": None,
                            "age": None,
                            "surname": "titi_new",
                            "nicknames": ["tonew", "tinew"],
                        },
                        {
                            "name": "toto_new",
                            "age": 22,
                            "surname": None,
                            "nicknames": None,
                        },
                    )

                    self.sub_test_delete(con, _id)

                    self.sub_test_select(con)

    def test_nolocal_copy_noexpire_update(self):
        """
        Test with local variables, copy, and no expire
        """
        for remote in CONNECTOR_REMOTE:
            for local in CONNECTOR_LOCAL:

                print(f"test with {remote[0]} -> {local[0]}")

                con = DBExtenderConnector(
                    "mix", remote[1], local[1], replicate_origin=True, sync_origin=True
                )
                with self.subTest(con=con):
                    self.sub_test_init_connector(con)
                    _id, _obj = self.sub_test_create(con)

                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": "toto",
                            "age": 22,
                            "surname": "titi",
                            "nicknames": ["to", "ti"],
                        },
                        {
                            "name": "toto",
                            "age": 22,
                            "surname": "titi",
                            "nicknames": ["to", "ti"],
                        },
                    )

                    self.sub_test_update(con, _id)

                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": "toto_new",
                            "age": 22,
                            "surname": "titi_new",
                            "nicknames": ["tonew", "tinew"],
                        },
                        {
                            "name": "toto_new",
                            "age": 22,
                            "surname": "titi_new",
                            "nicknames": ["tonew", "tinew"],
                        },
                    )

                    # check the remote is deleted too
                    origin_id = self.sub_test_delete(con, _id)
                    self.assertIsNotNone(origin_id)
                    with self.assertRaises(NotFoundError) as e:
                        con._origin_db_handler.delete_by_id(origin_id)
                    self.assertIn(
                        f'_id "{origin_id}" not found in', e.exception.to_string()
                    )

                    self.sub_test_select(con)

    def test_nolocal_copy_noexpire_noupdate(self):
        """
        Test with local variables, copy, and no expire
        """
        for remote in CONNECTOR_REMOTE:
            for local in CONNECTOR_LOCAL:

                print(f"test with {remote[0]} -> {local[0]}")

                con = DBExtenderConnector(
                    "mix", remote[1], local[1], replicate_origin=True, sync_origin=False
                )
                with self.subTest(con=con):
                    self.sub_test_init_connector(con)
                    _id, _obj = self.sub_test_create(con)

                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": "toto",
                            "age": 22,
                            "surname": "titi",
                            "nicknames": ["to", "ti"],
                        },
                    )

                    self.sub_test_update(con, _id)

                    self._check_keys(
                        con,
                        _id,
                        {
                            "name": "toto_new",
                            "age": 22,
                            "surname": "titi_new",
                            "nicknames": ["tonew", "tinew"],
                        },
                    )

                    origin_id = self.sub_test_delete(con, _id)
                    self.assertIsNone(origin_id)

                    self.sub_test_select(con)
