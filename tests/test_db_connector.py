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
    Int,
    Dict,
    List,
    Bool,
    RefsList,
    DeleteStrategy,
)
from backo import SFilter, Operator, DBError
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

YML_DIR = "/tmp/backo_tests_connector"
SQLITE3_DB = "/tmp/backo_tests_connector_sqlite3.db"
YML_FILE_DB = "/tmp/backo_yml_file.yml"


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
        rep, _mess = con.check_structure()
        self.assertEqual(rep, True)

        con.connect()

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
        u = con.get_by_id(_id)
        self.assertIsNotNone(u)
        self.assertEqual("age" in u, True)
        self.assertEqual("name" in u, True)
        self.assertEqual(u["age"], 12)

        con.delete_by_id(_id)

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

    def test_memory_connector(self):
        """
        create
        and delete errors
        """

        con = DBMemoryConnector("Memory")
        # con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, "Memory")

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, "Memory")

        con.close()

    def test_valkey_db_connector(self):
        """
        KeyDB connector
        """

        con = DBValkeyConnector("Redis", "redis://localhost:6379/0")
        # con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, "Redis")

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, "Redis")

        con.close()

    def test_yml_dir_connector(self):
        """
        create
        and delete errors
        """
        con = DBYmlDirConnector(YML_DIR)
        # con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_DIR)

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_DIR)

        con.close()

    def test_yml_connector_by_id_no_path(self):
        """
        test for yml connector by _id with no path
        """
        con = DBYmlConnector(YML_FILE_DB, db_path=["home", "sub"])

        # Create the structure
        con.check_structure(True)

        # check the structure
        must_be_ok, _mess = con.check_structure()
        self.assertEqual(must_be_ok, True)

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.close()

    def test_yml_connector_by_id_path(self):
        """
        test for yml connector by _id with a path
        """
        con = DBYmlConnector(YML_FILE_DB)

        # Create the structure
        con.check_structure(True)

        # check the structure
        must_be_ok, _mess = con.check_structure()
        self.assertEqual(must_be_ok, True)

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.close()

    def test_yml_connector_array_no_path(self):
        """
        test for yml connector in a list with no path
        """
        con = DBYmlConnector(YML_FILE_DB, by__id=False)

        # Create the structure
        con.check_structure(True)

        # check the structure
        must_be_ok, _mess = con.check_structure()
        self.assertEqual(must_be_ok, True)

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.close()

    def test_yml_connector_array_path(self):
        """
        test for yml connector in a list with no path
        """
        con = DBYmlConnector(YML_FILE_DB, by_id=False, db_path=["home", "sub2"])

        # Create the structure
        con.check_structure(True)

        # check the structure
        must_be_ok, _mess = con.check_structure()
        self.assertEqual(must_be_ok, True)

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

        with self.subTest(con=con):
            self.sub_test_crud_connector(con, YML_FILE_DB)

        con.close()

    def test_mongo_connector(self):
        """
        create
        and delete errors
        """
        con = DBMongoConnector("mongodb://localhost:27017/testMongo", "MyColl")
        # con.item_mapper.add_attribute_transformer("$.name", RenameTransformer("$.nom"))
        # con.item_mapper.add_attribute_mappers("$.name", MongoRenameMapper("$.nom"))

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
        self.assertEqual(len(res.items), 2)
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
        self.assertEqual(len(res.items), 0)

        con.register_transformer(RenameTransformer(["age"], ["age_in_db"]))
        con.register_transformer(IgnoreTransformer(["not", "exists"]))

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
        self.assertEqual(len(res.items), 2)
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

        con.close()

    def test_sqlite3_checker(self):
        """
        Test for sqlite3
        """
        con_users = DBSqlite3Connector(SQLITE3_DB, "users")
        con_sites = DBSqlite3Connector(SQLITE3_DB, "sites")

        backoffice = Backoffice("myApp")
        coll_users = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "age": Int(),
                    "nicknames": List(Dict({"a": String()})),
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

        # Add a transformater (for the fun)
        con_users.register_transformer(RenameTransformer(["age"], ["age_in_db"]))

        con_users.set_model(coll_users.get_meta())
        con_sites.set_model(coll_sites.get_meta())

        # Create the structure
        con_users.check_structure(True)

        # check the structure
        must_be_ok, _mess = con_users.check_structure()
        self.assertEqual(must_be_ok, True)

        # Create the structure
        con_sites.check_structure(True)

        # check the structure
        must_be_ok, _mess = con_sites.check_structure()
        self.assertEqual(must_be_ok, True)

        _id = con_users.create(
            {"name": "bebert", "nicknames": [{"a": "al"}, {"a": "bert"}], "age": 10}
        )
        self.assertIsNotNone(_id)
        u = con_users.get_by_id(_id)
        self.assertIsNotNone(u)

        self.assertEqual("age" in u, True)
        self.assertEqual("age_in_db" in u, False)

        # check filters
        where, values = con_users.filter.build_db_filter(
            SFilter("$.name", Operator.EQ, "zaza")
        )
        self.assertEqual(where, "( users.name == ?)")
        self.assertEqual(values, ("zaza",))

        where, values = con_users.filter.build_db_filter(
            SFilter(
                None,
                Operator.AND,
                [
                    SFilter("$.name", Operator.EQ, "zaza"),
                    SFilter("$.surname", Operator.EQ, "zozo"),
                ],
            )
        )
        self.assertEqual(where, "( ( users.name == ?) AND ( users.surname == ?) )")
        self.assertEqual(
            values,
            (
                "zaza",
                "zozo",
            ),
        )

        # with a list error
        with self.assertRaises(DBError) as e:
            con_users.filter.build_db_filter(
                SFilter("$.nicknames.a", Operator.EQ, "zaza")
            )
        self.assertEqual(
            e.exception.to_string(),
            "Filter in list not implemented (path=$.nicknames.a)",
        )

        # unknown path
        with self.assertRaises(DBError) as e:
            con_users.filter.build_db_filter(
                SFilter("$.notexists", Operator.EQ, "zaza")
            )
        self.assertEqual(
            e.exception.to_string(), "Wrong path $.notexists (doesnt exists in model)"
        )

        with self.subTest(con=con_users):
            self.sub_test_crud_connector(con_users, f"{SQLITE3_DB}(users)")
