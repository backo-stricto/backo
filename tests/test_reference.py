"""
test for References()
"""

# pylint: disable=too-many-lines, no-member, import-error, protected-access, wrong-import-order, duplicate-code, invalid-name

import os
import unittest
from backo import Item, Collection
from backo.db import DBYmlDirConnector

from backo import Backoffice
from backo import (
    Ref,
    RefsList,
    DeleteStrategy,
    FillStrategy,
    NotFoundError,
    BackoError,
    current_user,
)
from backo import String, Bool

YML_DIR = "/tmp/backo_tests_references"

yml_users = DBYmlDirConnector(os.path.join(YML_DIR, "Users"))
yml_users.generate_id = lambda o: f"User_{o["name"]}_{o["surname"]}"
# --- DB for sites
yml_sites = DBYmlDirConnector(os.path.join(YML_DIR, "Sites"))
yml_sites.generate_id = lambda o: f"Site_{o["name"]}"
# --- DB for humans
yml_humans = DBYmlDirConnector(os.path.join(YML_DIR, "Humans"))
yml_humans.generate_id = lambda o: f"Human_{o["name"]}"
# --- DB for animals
yml_animals = DBYmlDirConnector(os.path.join(YML_DIR, "Animals"))
yml_animals.generate_id = lambda o: f"Animal_{o["desc"]}"


o2m_ofs_ods_combinations = {
    "FM": (FillStrategy.FILL, DeleteStrategy.MUST_BE_EMPTY),
    "FD": (FillStrategy.FILL, DeleteStrategy.DELETE_REFERENCED_ITEMS),
    "FU": (FillStrategy.FILL, DeleteStrategy.UNLINK_REFERENCED_ITEMS),
    "NM": (FillStrategy.NOT_FILL, DeleteStrategy.MUST_BE_EMPTY),
    "ND": (FillStrategy.NOT_FILL, DeleteStrategy.DELETE_REFERENCED_ITEMS),
    "NU": (FillStrategy.NOT_FILL, DeleteStrategy.UNLINK_REFERENCED_ITEMS),
}

backoffices_o2m = {}

for st_name, st_values in o2m_ofs_ods_combinations.items():
    user = Item(
        {
            "name": String(),
            "surname": String(),
            "site": Ref(coll="sites", field="$.users"),
            "male": Bool(default=True),
        }
    )
    site = Item(
        {
            "name": String(),
            "address": String(),
            "users": RefsList(
                coll="users",
                field="$.site",
                ofs=st_values[0],
                ods=st_values[1],
            ),
        }
    )

    b = Backoffice(st_name)
    b.register_collection(Collection("users", user, yml_users))
    b.register_collection(Collection("sites", site, yml_sites))
    backoffices_o2m[st_name] = b

m2m_ofs_ods_combinations = {
    "FMFM": (
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "FMFD": (
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "FMFU": (
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "FMNM": (
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "FMND": (
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "FMNU": (
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "FDFM": (
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "FDFD": (
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "FDFU": (
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "FDNM": (
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "FDND": (
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "FDNU": (
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "FUFM": (
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "FUFD": (
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "FUFU": (
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "FUNM": (
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "FUND": (
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "FUNU": (
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "NMFM": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "NMFD": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "NMFU": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "NMNM": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "NMND": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "NMNU": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "NDFM": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "NDFD": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "NDFU": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "NDNM": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "NDND": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "NDNU": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "NUFM": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "NUFD": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "NUFU": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
    "NUNM": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.MUST_BE_EMPTY,
    ),
    "NUND": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.DELETE_REFERENCED_ITEMS,
    ),
    "NUNU": (
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
        FillStrategy.NOT_FILL,
        DeleteStrategy.UNLINK_REFERENCED_ITEMS,
    ),
}

backoffices_m2m = {}

for st_name, st_values in m2m_ofs_ods_combinations.items():
    human = Item(
        {
            "name": String(),
            "totems": RefsList(
                coll="animals",
                field="$.humans",
                ofs=st_values[0],
                ods=st_values[1],
            ),
        }
    )

    animal = Item(
        {
            "desc": String(),
            "humans": RefsList(
                coll="humans",
                field="$.totems",
                ofs=st_values[2],
                ods=st_values[3],
            ),
        }
    )

    b = Backoffice(st_name)
    b.register_collection(Collection("humans", human, yml_humans))
    b.register_collection(Collection("animals", animal, yml_animals))
    backoffices_m2m[st_name] = b


o2o_require_combinations = {"FF": (False, False), "FT": (False, True)}

backoffices_o2o = {}

for st_name, st_values in o2o_require_combinations.items():
    human = Item(
        {
            "name": String(),
            "totem": Ref(coll="animals", field="$.human", required=st_values[0]),
        }
    )

    animal = Item(
        {
            "desc": String(),
            "human": Ref(coll="humans", field="$.totem", required=st_values[1]),
        }
    )

    b = Backoffice(st_name)
    b.register_collection(Collection("humans", human, yml_humans))
    b.register_collection(Collection("animals", animal, yml_animals))
    backoffices_o2o[st_name] = b


class TestReferences(unittest.TestCase):
    """
    Test for references (Ref and RefsList)

    """

    def setUp(self):
        """setup"""
        current_user.standalone = True
        yml_animals.drop()
        yml_humans.drop()
        yml_sites.drop()
        yml_users.drop()
        return super().setUp()

    def sub_test_crud_o2m(self, backoffice: Backoffice):
        """
        CRUD One 2 many

        """
        yml_sites.drop()
        yml_users.drop()

        s1 = backoffice.sites.create({"name": "moon", "address": "far"})
        s2 = backoffice.sites.create({"name": "mars", "address": "farfar"})
        u1 = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": s1._id}
        )
        u2 = backoffice.users.create(
            {"name": "bebert", "surname": "elon", "site": s2._id}
        )

        # -- Check if reverse is filled
        s1.reload()
        self.assertEqual(len(s1.users), 1)
        self.assertEqual(s1.users[0], u1._id)
        u1.reload()
        u1.site = s2._id
        u1.save()
        s1.reload()
        self.assertEqual(len(s1.users), 0)

        # Check select follow object
        a = u1.select("$.site")
        self.assertEqual( type(a), Ref )
        a = u1.select("$.site.")
        self.assertEqual( type(a), Item )

        s1.delete()
        s2.reload()
        self.assertEqual(len(s2.users), 2)

        a = s2.select("$.users")
        self.assertEqual( type(a), RefsList )
        a = s2.select("$.users.")
        self.assertEqual( type(a), list )
        self.assertEqual( len(a), 2 )
        self.assertEqual( type(a[0]), Item )
        self.assertEqual( type(a[1]), Item )

        a = s2.select("$.users[-1].")
        self.assertEqual( type(a), Item )

        a = s2.select("$.users[-1].name")
        self.assertEqual( a, "bebert" )


        a = s2.select("$.users[0:2].")
        self.assertEqual( type(a), list )

        
        a = s2.select("$.users[0].")
        self.assertEqual( type(a), Item )



        u2.delete()
        s2.reload()
        self.assertEqual(len(s2.users), 1)

    def test_crud_o2m(self):
        """
        Wrapper CRUD One to many
        """
        for backoffice in backoffices_o2m.values():
            with self.subTest(backoffice=backoffice):
                self.sub_test_crud_o2m(backoffice)

    def test_references_o2m_FM(self):
        """
        Fill Strategy - MUST_BE_EMPTY
        """
        backoffice = backoffices_o2m["FM"]

        si = backoffice.sites.create({"name": "moon", "address": "far"})
        _u = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": si._id}
        )

        # -- delete site error
        si.reload()
        with self.assertRaises(BackoError) as e:
            si.delete()
        self.assertEqual(
            e.exception.to_string(),
            'Collection "users" not empty',
        )

    def test_references_o2m_FFD(self):
        """
        Fill Strategy - DELETE_REFERENCED_ITEMS
        """
        backoffice = backoffices_o2m["FD"]

        si = backoffice.sites.create({"name": "moon", "address": "far"})
        u = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": si._id}
        )

        # -- delete site
        si.reload()
        si.delete()

        with self.assertRaises(NotFoundError) as e:
            u.reload()
        self.assertEqual(
            e.exception.to_string(),
            '_id "User_bebert_bebert" not found in "/tmp/backo_tests_references/Users"',
        )

    def test_references_o2m_FFU(self):
        """
        Fill Strategy - UNLINK_REFERENCED_ITEMS
        """
        backoffice = backoffices_o2m["FU"]

        si = backoffice.sites.create({"name": "moon", "address": "far"})

        u = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": si._id}
        )

        # -- delete site
        si.reload()
        si.delete()
        u.reload()
        self.assertIsNone(u.site.get_value())

    def test_references_o2m_FNM(self):
        """
        Not Fill Strategy - MUST_BE_EMPTY
        """
        backoffice = backoffices_o2m["NM"]

        si = backoffice.sites.create({"name": "moon", "address": "far"})
        _u = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": si._id}
        )

        # -- delete site error
        si.reload()
        with self.assertRaises(BackoError) as e:
            si.delete()
        self.assertEqual(
            e.exception.to_string(),
            'Collection "users" not empty',
        )

    def test_references_o2m_FND(self):
        """
        Not Fill Strategy - DELETE_REFERENCED_ITEMS
        """
        backoffice = backoffices_o2m["ND"]

        si = backoffice.sites.create({"name": "moon", "address": "far"})
        u = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": si._id}
        )

        # -- delete site
        si.reload()
        si.delete()

        with self.assertRaises(NotFoundError) as e:
            u.reload()
        self.assertEqual(
            e.exception.to_string(),
            '_id "User_bebert_bebert" not found in "/tmp/backo_tests_references/Users"',
        )

    def test_references_o2m_FNU(self):
        """
        Not - Fill Strategy - UNLINK_REFERENCED_ITEMS
        """
        backoffice = backoffices_o2m["NU"]

        si = backoffice.sites.create({"name": "moon", "address": "far"})

        u = backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": si._id}
        )

        # -- delete site
        si.reload()
        si.delete()
        u.reload()
        self.assertIsNone(u.site.get_value())

    def sub_test_crud_m2m(self, backoffice: Backoffice):
        """
        CRUD for many to many (RefsList)

        """
        yml_humans.drop()
        yml_animals.drop()

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        # -- Check if reverse is filled
        a1.reload()
        self.assertEqual(len(a1.humans), 1)
        a2.reload()
        self.assertEqual(len(a2.humans), 1)

        # Change
        h1.totems.append(a2._id)
        h1.save()
        h1.reload()
        self.assertEqual(len(h1.totems), 2)

        a1.reload()
        self.assertEqual(len(a1.humans), 1)

        a2.reload()
        self.assertEqual(len(a2.humans), 2)

        # Change from animals
        a1.humans = []
        a1.save()
        h1.reload()
        self.assertEqual(len(h1.totems), 1)
        h2.reload()
        self.assertEqual(len(h2.totems), 1)

        # Delete an empty
        a1.delete()
        h1.reload()
        self.assertEqual(len(h1.totems), 1)
        h2.reload()
        self.assertEqual(len(h2.totems), 1)

    def test_crud_m2m(self):
        """
        wrapper many to many CRUD
        """
        for backoffice in backoffices_m2m.values():
            with self.subTest(backoffice=backoffice):
                self.sub_test_crud_m2m(backoffice)

    def test_references_m2m_FMFM(self):
        """
        Fill - MUST_BE_EMPTY - Fill  - MUST_BE_EMPTY
        """

        backoffice = backoffices_m2m["FMFM"]

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        _h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        _h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        a1.reload()
        with self.assertRaises(BackoError) as e:
            a1.delete()
        self.assertEqual(
            e.exception.to_string(),
            'Collection "humans" not empty',
        )

    def test_references_m2m_FMNM(self):
        """
        Fill - MUST_BE_EMPTY - NOT_Fill  - MUST_BE_EMPTY
        """
        backoffice = backoffices_m2m["FMNM"]

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        _h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        _h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        a1.reload()
        with self.assertRaises(BackoError) as e:
            a1.delete()
        self.assertEqual(
            e.exception.to_string(),
            'Collection "humans" not empty',
        )

    def test_references_m2m_FMFU(self):
        """
        Fill - MUST_BE_EMPTY - Fill - UNLINK
        """
        backoffice = backoffices_m2m["FMFU"]

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        _h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        a1.reload()
        a1.delete()
        h1.reload()
        self.assertEqual(len(h1.totems), 0)

    def test_references_m2m_FMNU(self):
        """
        Fill - MUST_BE_EMPTY - NOT_Fill - UNLINK
        """
        backoffice = backoffices_m2m["FMNU"]

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        _h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        a1.reload()
        a1.delete()
        h1.reload()
        self.assertEqual(len(h1.totems), 0)

    def test_references_m2m_FMFD(self):
        """
        Fill - MUST_BE_EMPTY - Fill - DELETE
        """
        backoffice = backoffices_m2m["FMFD"]

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        _h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        a1.reload()
        a1.delete()
        with self.assertRaises(NotFoundError) as e:
            h1.reload()
        self.assertEqual(
            e.exception.to_string(),
            '_id "Human_parker" not found in "/tmp/backo_tests_references/Humans"',
        )

    def test_references_m2m_FMND(self):
        """
        Fill - MUST_BE_EMPTY - NOT_Fill - DELETE
        """
        backoffice = backoffices_m2m["FMND"]

        a1 = backoffice.animals.create({"desc": "ant"})
        a2 = backoffice.animals.create({"desc": "spider"})
        h1 = backoffice.humans.create({"name": "parker", "totems": [a1._id]})
        _h2 = backoffice.humans.create({"name": "pym", "totems": [a2._id]})

        a1.reload()
        a1.delete()
        with self.assertRaises(NotFoundError) as e:
            h1.reload()
        self.assertEqual(
            e.exception.to_string(),
            '_id "Human_parker" not found in "/tmp/backo_tests_references/Humans"',
        )

    def sub_test_crud_o2o(self, backoffice: Backoffice):
        """
        test crud one to one for this backoffice
        """
        yml_humans.drop()
        yml_animals.drop()

        h1 = backoffice.humans.create({"name": "parker"})
        h2 = backoffice.humans.create({"name": "pym"})
        h3 = backoffice.humans.create({"name": "parker2"})
        a1 = backoffice.animals.create({"desc": "spider", "human": h1._id})
        a2 = backoffice.animals.create({"desc": "ant", "human": h2._id})

        # -- Check if reverse is filled
        h1.reload()
        self.assertEqual(h1.totem, a1._id)
        h2.reload()
        self.assertEqual(h2.totem, a2._id)

        # Change spider -> parker 2, so parker is alone
        a1.human = h3._id
        a1.save()
        h3.reload()
        self.assertEqual(h3.totem, a1._id)
        h1.reload()
        self.assertEqual(h1.totem, None)

    def test_crud_o2o(self):
        """
        CRUD operations on one to one ref
        """
        for backoffice in backoffices_o2o.values():
            with self.subTest(backoffice=backoffice):
                self.sub_test_crud_o2o(backoffice)
