"""
test for DBConnectors
"""

# pylint: disable=too-many-statements, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
from datetime import datetime, timedelta
from backo import (
    NotFoundError,
    Backoffice,
    Collection,
    Item,
    String,
    FillStrategy,
    Ref,
    Int,
    Dict,
    Float,
    List,
    Bool,
    Datetime,
    RefsList,
    DeleteStrategy,
    current_user,
    #log_system,
    #LogLevel,
)
from backo import SFilter, Operator
from backo.db import (
    DBHandler,
    SelectResponse,
    DBMemoryConnector,
    DBYmlDirConnector,
    DBMongoConnector,
    DBSqlite3Connector,
    DBYmlConnector,
    DBValkeyConnector,
    RenameTransformer,
    IgnoreTransformer,
)

FULL_USER = Item(
    {
        "name": String(),
        "surname": String(),
        "age": Int(),
        "date": Datetime(),
        "nicknames": List(String()),
        "nationalities": List(Dict({"country": String()})),
        "site": Ref(coll="sites", field="$.users", ofs=FillStrategy.NOT_FILL),
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

ALL_CONNECTOR_USERS = [
    ("Memory", DBMemoryConnector("Memory"), False),
    ("Redis", DBValkeyConnector("Redis", "redis://localhost:6379/0"), False),
    (YML_DIR, DBYmlDirConnector(YML_DIR), False),
    (YML_FILE_DB, DBYmlConnector(YML_FILE_DB), False),
    (
        YML_FILE_DB,
        DBYmlConnector(YML_FILE_DB, by_id=False, db_path=["home", "sub2"]),
        False,
    ),
    (YML_FILE_DB, DBYmlConnector(YML_FILE_DB, db_path=["home", "sub"]), False),
    ("users", DBMongoConnector("mongodb://localhost:27017/testMongo", "users"), True),
    ("users", DBSqlite3Connector(SQLITE3_DB, "users"), True),
]
ALL_CONNECTOR_SITES = [
    ("Memory", DBMemoryConnector("Memory"), False),
    ("Redis", DBValkeyConnector("Redis", "redis://localhost:6379/1"), False),
    (YML_DIR_SITE, DBYmlDirConnector(YML_DIR_SITE), False),
    (YML_FILE_DB_SITE, DBYmlConnector(YML_FILE_DB_SITE), False),
    (
        YML_FILE_DB_SITE,
        DBYmlConnector(YML_FILE_DB_SITE, by_id=False, db_path=["home", "sub2"]),
        False,
    ),
    (
        YML_FILE_DB_SITE,
        DBYmlConnector(YML_FILE_DB_SITE, db_path=["home", "sub"]),
        False,
    ),
    ("sites", DBMongoConnector("mongodb://localhost:27017/testMongo", "sites"), True),
    ("sites", DBSqlite3Connector(SQLITE3_DB, "sites"), True),
]

CONNECTOR_USERS = ALL_CONNECTOR_USERS  # [7:8]
CONNECTOR_SITES = ALL_CONNECTOR_SITES  # [7:8]

NOW = datetime.now().replace(microsecond=0)


class TestDBConnector(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        # log = log_system.get_or_create_logger("DBSqlite3Connector")
        # log.setLevel(LogLevel.DEBUG)

        super().__init__(*args, **kwargs)

    def sub_test_init_connector(self, con: DBHandler, schema: dict):
        """
        test Initialisation for every DBHandler

        """
        con.set_model(schema)

        # Built the structure
        con.check_structure(True)

        # check the structure
        rep, _mess = con.check_structure()
        self.assertEqual(rep, True)

        # Drop
        con.drop()

    def sub_test_crud_connector(self, con: DBHandler, _db_name: str):
        """
        test CRUD for every DBHandler

        """
        _id = con.create({"name": "toto", "age": 22})
        self.assertIsNotNone(_id)

        e = con.get_by_id(_id)
        self.assertEqual(e["_id"], _id)
        self.assertEqual(e["name"], "toto")
        self.assertEqual(e["age"], 22)

        # create / delete
        _id = con.create({"name": "toto2", "age": 12})
        self.assertIsNotNone(_id)
        u = con.get_by_id(_id)
        self.assertIsNotNone(u)
        self.assertEqual("age" in u, True)
        self.assertEqual("name" in u, True)
        self.assertEqual(u["age"], 12)

        con.delete_by_id(_id)

        # get error not found
        with self.assertRaises(NotFoundError) as e:
            con.get_by_id(_id)
        self.assertIn(f'_id "{_id}" not found in', e.exception.to_string())

        # delete error not found
        with self.assertRaises(NotFoundError) as e:
            con.delete_by_id(_id)
        self.assertIn(f'_id "{_id}" not found in', e.exception.to_string())

        # create and select
        _id = con.create({"name": "toto2", "age": 12})
        self.assertIsNotNone(_id)
        res = con.select(SFilter("$.name", Operator.EQ, "toto"))
        self.assertEqual(type(res), SelectResponse)
        self.assertGreaterEqual(len(res.items), 1)
        self.assertGreaterEqual(res.total, 1)

        # update
        con.save(_id, {"name": "toto2", "age": 13})
        u = con.get_by_id(_id)
        self.assertIsNotNone(u)
        self.assertEqual("age" in u, True)
        self.assertEqual("name" in u, True)
        self.assertEqual(u["age"], 13)

        res = con.select(SFilter("$.name", Operator.EQ, "toto"))
        self.assertEqual(type(res), SelectResponse)
        self.assertGreaterEqual(len(res.items), 1)

        res = con.select(SFilter("$.age", Operator.GTE, 13))
        self.assertEqual(type(res), SelectResponse)
        self.assertGreaterEqual(len(res.items), 1)

    def sub_test_select_connector(
        self, con: DBHandler, _db_name: str, handle_sfilter: bool
    ):
        """
        test the connector on selections

        :param con: The connector to test
        :type con: DBHandler
        :param db_name: just a name
        :type db_name: str
        :param handle_sfilter: if the filter handler SFilter or not
        :type handle_sfilter: bool
        """
        max_item = 50

        rep, _mess = con.check_structure()
        self.assertEqual(rep, True)

        con.connect()
        con.drop()

        # Insert into the database
        for i in range(0, max_item):
            _id = con.create({"name": f"rambo_{i}", "surname": f"Mickey_{i}", "age": i})
            self.assertIsNotNone(_id)

        # Select All
        res = con.select(None)
        self.assertEqual(type(res), SelectResponse)
        self.assertGreaterEqual(len(res.items), max_item)
        res = con.select(SFilter(None, Operator.TRUE, None))
        self.assertEqual(type(res), SelectResponse)
        self.assertGreaterEqual(len(res.items), max_item)

        if handle_sfilter:

            res = con.select(SFilter("$.name", Operator.EQ, "rambo_1"))
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), 1)

            res = con.select(SFilter("$.age", Operator.NE, 1))
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), max_item - 1)

            res = con.select(SFilter("$.age", Operator.GT, 2))
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), max_item - 3)

            res = con.select(SFilter("$.age", Operator.GTE, 2))
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), max_item - 2)

            res = con.select(
                SFilter(
                    None,
                    Operator.AND,
                    [
                        SFilter("$.name", Operator.EQ, "rambo_1"),
                        SFilter("$.age", Operator.GTE, 1),
                    ],
                )
            )
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), 1)
            res = con.select(
                SFilter(
                    None,
                    Operator.OR,
                    [
                        SFilter("$.age", Operator.LTE, 13),
                        SFilter("$.age", Operator.GTE, 18),
                    ],
                )
            )
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), max_item - 4)
            res = con.select(
                SFilter(
                    None,
                    Operator.AND,
                    [
                        SFilter("$.age", Operator.LTE, 13),
                        SFilter("$.age", Operator.GTE, 18),
                    ],
                )
            )
            self.assertEqual(type(res), SelectResponse)
            self.assertEqual(len(res.items), 0)

    def sub_test_backo_connector(self, con_users: DBHandler, con_sites: DBHandler):
        """
        Test with backo with 2 collections ("users" and "sites"), one in each DBHandler

        :param con_users: DBHandler for users
        :type con_users: DBHandler
        :param con_sites: DBHandler for sites
        :type con_sites: DBHandler
        """

        print(f"Test backo for users in {type(con_users)}, sites in {type(con_sites)}")

        backoffice = Backoffice("myApp")
        coll_users = Collection(
            "users",
            FULL_USER,
            con_users,
        )
        backoffice.register_collection(coll_users)

        # --- DB for sites
        coll_sites = Collection(
            "sites",
            FULL_SITE,
            con_sites,
        )
        backoffice.register_collection(coll_sites)

        self.sub_test_init_connector(con_users, FULL_USER.get_schema())
        self.sub_test_init_connector(con_sites, FULL_SITE.get_schema())

        current_user.standalone = True

        # Creation
        user_idx = 0
        for i in range(0, 3):
            s = backoffice.sites.new()
            s.create(
                {
                    "name": f"place_{i}",
                    "address": f"here_{i}",
                    "weather": {"sun": 10.0 * i},
                }
            )
            s.reload()

            for _j in range(0, 3):
                v = backoffice.users.new()
                v.create(
                    {
                        "name": f"bebert_{user_idx}",
                        "surname": f"bebert_{user_idx}",
                        "date": NOW + timedelta(minutes=user_idx),
                        "nicknames": [f"the_b_{user_idx}", f"best_{user_idx}"],
                        "nationalities": [{"country": "fr"}],
                        "site": s._id.get_value(),
                    }
                )
                self.assertEqual(type(v._id.get_value()), str)
                uu = backoffice.users.get_by_id(v._id.get_value())
                self.assertEqual(uu._id, v._id)

                user_idx += 1

        # Selections
        sel = backoffice.users.select(SFilter("$.name", Operator.EQ, "bebert_1"))
        self.assertEqual(type(sel), list)
        self.assertEqual(len(sel), 1)

        user = sel[0]

        uu = backoffice.users.get_by_id(user._id.get_value())
        self.assertEqual(uu._id, user._id)

        self.assertEqual(user.select("$.name"), "bebert_1")
        self.assertEqual(user.select("$.male"), True)
        self.assertEqual(user.select("$.site.name"), "place_0")
        self.assertEqual(type(user.nicknames), List)
        self.assertEqual(user.nicknames[0], "the_b_1")
        self.assertEqual(type(user.nationalities), List)
        self.assertEqual(len(user.nationalities), 1)
        self.assertEqual(user.nationalities[0].country, "fr")

        # update
        user.name = "new_bebert_1"
        user.nationalities.append({"country": "en"})
        user.save()
        self.assertEqual(user.select("$.name"), "new_bebert_1")
        self.assertEqual(user.select("$.male"), True)
        self.assertEqual(user.select("$.site.name"), "place_0")
        self.assertEqual(type(user.nicknames), List)
        self.assertEqual(user.nicknames[0], "the_b_1")
        self.assertEqual(type(user.nationalities), List)
        self.assertEqual(len(user.nationalities), 2)
        self.assertEqual(user.nationalities[0].country, "fr")
        self.assertEqual(user.nationalities[1].country, "en")

        sel = backoffice.sites.select(SFilter("$.weather.sun", Operator.GT, 1.5))
        self.assertEqual(type(sel), list)
        self.assertEqual(len(sel), 2)

        d = NOW + timedelta(minutes=4)

        sel = backoffice.users.select(SFilter("$.date", Operator.GT, d))
        self.assertEqual(type(sel), list)
        self.assertEqual(len(sel), 4)

        sel = backoffice.users.select(SFilter("$.date", Operator.GT, d.isoformat()))
        self.assertEqual(type(sel), list)
        self.assertEqual(len(sel), 4)

    def test_connector_sample(self):
        """
        Do a CRUD AND some SELECT directly on a Connector
        """
        for con_name, con, handle_sfilter in CONNECTOR_USERS:

            print(f"Test test_connector_sample {type(con)}")
            con.connect()
            with self.subTest(con=con):
                self.sub_test_init_connector(con, FULL_USER.get_schema())
                self.sub_test_crud_connector(con, con_name)
                self.sub_test_select_connector(con, con_name, handle_sfilter)

            con.close()

    def test_connector_with_transformer(self):
        """
        Do a CRUD AND some SELECT directly on a Connector
        """
        for con_name, con, handle_sfilter in CONNECTOR_USERS:

            print(f"Test test_connector_with_transformer {type(con)}")

            con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
            con.register_transformer(IgnoreTransformer(["not", "exists"]))
            con.connect()

            with self.subTest(con=con):
                self.sub_test_init_connector(con, FULL_USER.get_schema())
                self.sub_test_crud_connector(con, con_name)
                self.sub_test_select_connector(con, con_name, handle_sfilter)

            con.close()


    def test_connector_backo(self):
        """
        Do a CRUD on a sample COnnector
        """

        for _con_user_name, con_user, _user_handle_sfilter in ALL_CONNECTOR_USERS:
            con_user.connect()
            for _con_site_name, con_site, _site_handle_sfilter in ALL_CONNECTOR_SITES:
                con_site.connect()

        for _con_user_name, con_user, _user_handle_sfilter in CONNECTOR_USERS:
            for _con_site_name, con_site, _site_handle_sfilter in CONNECTOR_SITES:
                with self.subTest(con_users=con_user, con_sites=con_site):
                    self.sub_test_backo_connector(con_user, con_site)

        for _con_user_name, con_user, _user_handle_sfilter in ALL_CONNECTOR_USERS:
            con_user.close()
            for _con_site_name, con_site, _site_handle_sfilter in ALL_CONNECTOR_SITES:
                con_site.close()
