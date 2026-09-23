"""
test for Flask and routes
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code, too-many-public-methods
import multiprocessing
import time
from flask import Flask

# get the resources folder in the tests folder

from backo import Item, Collection
from backo.db import DBYmlDirConnector, DBBackoRedirectConnector
from backo import Backoffice, current_user

from backo import String, Bool

from .test_routes import TestRoutes

YML_DIR = "/tmp/backo_tests_routes_23"
yml_users2 = DBYmlDirConnector(YML_DIR)
yml_users2.generate_id = lambda o: f"User_{o["name"]}_{o["surname"]}"


def launch_backoffice2():
    """
    Launching the second backoffice in background with the same
    database
    """

    # ignore sessions for this campaign of tests.
    current_user.standalone = True

    users2_coll = Collection(
        "users2",
        Item(
            {
                "name": String(),
                "surname": String(),
                "male": Bool(
                    default=True,
                ),
            }
        ),
        yml_users2,
    )
    backo2 = Backoffice("backo2")
    backo2.register_collection(users2_coll)

    backo2.users2.create({"name": "bebert", "surname": "bebert"})
    backo2.users2.create({"name": "bert1", "surname": "bert1"})
    backo2.users2.create({"name": "bert2", "surname": "bert2"})

    flask2 = Flask("backo2")
    backo2.build_routes(flask2)
    flask2.run(host="0.0.0.0", port=5050)


process_backo_2 = multiprocessing.Process(target=launch_backoffice2, args=())


def start_backo2():
    """
    Start the second backo server
    """
    if not process_backo_2.is_alive():
        process_backo_2.start()
        time.sleep(1)


def stop_backo2():
    """
    Stop the second backo server
    """
    if process_backo_2.is_alive():
        process_backo_2.terminate()


class TestRestApiConnector(TestRoutes):
    """
    TestRestApiConnector do all tests from TestRoutes, with a redirect to another backo server

    :param TestRoutes: _description_
    :type TestRoutes: _type_
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        db_handler = DBBackoRedirectConnector(
            "users2",
            host="localhost",
            port=5050,
            tls=False,
            prefix="backo2",
        )
        db_handler.set_model(self.backo.users.model.get_schema())
        self.backo.users.db_handler = db_handler
        self.backo.users.model.set_db_handler(db_handler)

    def setUp(self):

        current_user.standalone = True

    @classmethod
    def setUpClass(cls):

        start_backo2()

    @classmethod
    def tearDownClass(cls):
        stop_backo2()
