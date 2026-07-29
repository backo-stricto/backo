"""
test for DBConnectors
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest


from backo import (
    NotFoundError,
    Backoffice,
    Collection,
    Item,
    String,
    FillStrategy,
    Ref,
    Dict,
    Int,
    List,
    Bool,
    RefsList,
    DeleteStrategy,
)
from backo import SFilter, Operator
from backo.db import DBHandler, RenameTransformer
from backo.db import (
    DBMemoryConnector,
    DBYmlDirConnector,
    DBMongoConnector,
    MongoRenameMapper,
    Sqlite3AttributeMapper,
    DBSqlite3Connector,
    SqlDBChecker,
)

YML_DIR = "/tmp/backo_tests_connector"
SQLITE3_DB = "/tmp/backo_tests_connector_sqlite3.db"


class TestDBConnector(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

    def sub_test_crud_connector(self, con: DBHandler, db_name: str):
        """
        test CRUD for every DBHandler
        """
        con.drop()
        _id = con.create({"name": "toto", "age": 22})
        self.assertIsNotNone(_id)

        e = con.get_by_id(_id)
        self.assertEqual(e["_id"], _id)
        self.assertEqual(e["name"], "toto")
        self.assertEqual(e["age"], 22)

        # create / delete
        _id = con.create({"name": "toto2", "age": 12})
        self.assertIsNotNone(_id)
        rep = con.delete_by_id(_id)
        self.assertEqual(rep, True)

        # get error not found
        with self.assertRaises(NotFoundError) as e:
            con.get_by_id(_id)
        self.assertEqual(
            e.exception.to_string(),
            f'_id "{_id}" not found in "{db_name}"',
        )

        # delete error not found
        with self.assertRaises(NotFoundError) as e:
            con.delete_by_id(_id)
        self.assertEqual(
            e.exception.to_string(),
            f'_id "{_id}" not found in "{db_name}"',
        )

        # create and select
        _id = con.create({"name": "toto2", "age": 12})
        self.assertIsNotNone(_id)
        res = con.select(SFilter("$.name", Operator.EQ, "toto"))
        self.assertEqual(type(res), list)
        self.assertGreaterEqual(len(res), 1)

        # con.close()

    def test_memory_connector(self):
        """
        create
        and delete errors
        """

        con = DBMemoryConnector("Memory")
        con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, "Memory")

        con.close()

    def test_yml_dir_connector(self):
        """
        create
        and delete errors
        """
        con = DBYmlDirConnector(YML_DIR)
        con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_DIR)

        con.close()

    def test_mongo_connector(self):
        """
        create
        and delete errors
        """
        con = DBMongoConnector("mongodb://localhost:27017/testMongo", "MyColl")
        con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))
        con.item_mapper.add_attribute_mappers("$.name", MongoRenameMapper("$.nom"))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, "MyColl")

        res = con.select(
            SFilter(
                None,
                Operator.AND,
                [
                    SFilter("$.name", Operator.EQ, "toto"),
                    SFilter("$.age", Operator.GTE, 18),
                ],
            )
        )
        self.assertEqual(type(res), list)
        self.assertEqual(len(res), 1)
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
        self.assertEqual(len(res), 2)
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
        self.assertEqual(len(res), 0)

        con.close()

    def test_sqlite3_checker(self):

        con_users = DBSqlite3Connector(SQLITE3_DB, "users")
        con_sites = DBSqlite3Connector(SQLITE3_DB, "sites")

        backoffice = Backoffice("myApp")
        coll_users = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "nicknames": List(String()),
                    "site": Ref(
                        coll="sites", field="$.users", ofs=FillStrategy.NOT_FILL
                    ),
                    "male": Bool(default=True),
                }
            ),
            con_users,
        )

        backoffice.register_collection(coll_users)

        # --- DB for sites

        coll_sites = Collection(
            "sites",
            Item(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.DELETE_REFERENCED_ITEMS,
                    ),
                }
            ),
            con_sites,
        )

        backoffice.register_collection(coll_sites)

        checker = SqlDBChecker()
        checker.set_db_handler(coll_users.db_handler)
        checker.check_compliance("users", coll_users.get_meta())
        checker.check_compliance("sites", coll_sites.get_meta())

        # coll_users.db_handler.check_compliance(coll_users.get_meta())
        # coll_sites.db_handler.check_compliance(coll_sites.get_meta())
