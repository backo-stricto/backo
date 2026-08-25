"""
test for Selections()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
from backo import Item, Collection
from backo.db import DBYmlDirConnector
from backo import Backoffice
from backo import current_user, Selection
from backo import String, Bool, SFilter, Operator

### --- For development ---
# import logging
# from backo import log_system
# log_system.setLevel(logging.DEBUG)
# log_system.add_handler(log_system.set_streamhandler())
# log = log_system.get_or_create_logger("testing")


YML_DIR = "/tmp/backo_tests_selections"


class TestSelections(unittest.TestCase):
    """
    DB with references ()
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.yml_users = DBYmlDirConnector(YML_DIR)
        self.yml_users.generate_id = lambda o: f"User_{o["name"]}_{o["surname"]}"
        # self.yml_users = DBYmlConnector(path=YML_DIR)
        # self.yml_users.generate_id = (
        #     lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        # )

        self.backo = Backoffice("myApp")
        self.users = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "male": Bool(default=True),
                }
            ),
            self.yml_users,
        )

        self.backo.register_collection(self.users)

        self.yml_users.drop()
        current_user.standalone = True

    def test__all_selection(self):
        """
        creating an backoffice with ref one to many
        and use selectors to cross
        """

        self.yml_users.drop()
        u = self.backo.users.create({"name": "paul", "surname": "bebert"})
        self.assertEqual(u._id, "User_paul_bebert")

        u = self.backo.users.create({"name": "bert1", "surname": "bert1"})
        self.assertEqual(u._id, "User_bert1_bert1")

        u = self.backo.users.create({"name": "bert2", "surname": "bert2"})
        self.assertEqual(u._id, "User_bert2_bert2")

        rep = self.users._selections["_all"].select()
        self.assertEqual(rep["total"], 3)

        rep = self.users._selections["_all"].select(
            SFilter("$.name", Operator.EQ, "bert2")
        )
        self.assertEqual(rep["total"], 1)

        rep = self.users._selections["_all"].select(
            SFilter("$.male", Operator.EQ, True)
        )
        self.assertEqual(rep["total"], 3)

        rep = self.users._selections["_all"].select(
            SFilter("$.name", Operator.REG, r"bert.*")
        )
        self.assertEqual(rep["total"], 2)

    def test_multi_selection(self):
        """
        test selection with multi projections
        """

        self.yml_users.drop()
        u = self.backo.users.create({"name": "paul", "surname": "bebert"})
        self.assertEqual(u._id, "User_paul_bebert")

        u = self.backo.users.create({"name": "bert1", "surname": "bert1"})
        self.assertEqual(u._id, "User_bert1_bert1")

        u = self.backo.users.create({"name": "bert2", "surname": "bert2"})
        self.assertEqual(u._id, "User_bert2_bert2")

        my_selection = Selection(["$.name", "$.male"])
        self.users.register_selection("myselection", my_selection)

        rep = self.users._selections["myselection"].select()
        self.assertEqual(rep["total"], 3)
        rep = self.users._selections["myselection"].select(
            SFilter("$.surname", Operator.EQ, "bebert")
        )
        self.assertEqual(rep["total"], 1)
        self.assertEqual(rep["result"][0], ["User_paul_bebert", "paul", True])

    def test_selection_with_filters(self):
        """
        test selection with multi projections
        """

        self.yml_users.drop()
        u = self.backo.users.create({"name": "paul", "surname": "bebert"})
        self.assertEqual(u._id, "User_paul_bebert")

        u = self.backo.users.create({"name": "bert1", "surname": "bert1"})
        self.assertEqual(u._id, "User_bert1_bert1")

        u = self.backo.users.create({"name": "bert2", "surname": "bert2"})
        self.assertEqual(u._id, "User_bert2_bert2")

        my_selection = Selection(
            ["$.name", "$.male"], filter=SFilter("$.name", Operator.REG, r"bert")
        )

        self.users.register_selection("ms", my_selection)

        rep = self.users._selections["ms"].select()
        self.assertEqual(rep["total"], 2)
        rep = self.users._selections["ms"].select(
            SFilter("$.surname", Operator.EQ, "bert2")
        )
        self.assertEqual(rep["total"], 1)
        self.assertEqual(rep["result"][0], ["User_bert2_bert2", "bert2", True])
