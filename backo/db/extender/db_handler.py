# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
DBHandler for Multiplex
"""

from copy import deepcopy
from datetime import timedelta, datetime
from jsonpath import patch, findall

from stricto import (
    SFilter,
    Operator,
    Kparse,
    validation_parameters,
    Datetime,
    String,
    Selector,
)

from ..generic.db_handler import DBHandler
from ...error import DBError
from ..generic.transformer import Transformer
from ..generic.interface import SelectResponse

from ...sort import Sort
from ...log import log_system

log = log_system.get_or_create_logger("DBMultiplexconnector")


KPARSE_MODEL = {
    "local": {"type": list[str], "default": []},
    "expire": timedelta,
    "sync_origin": {"type": bool, "default": False},
    "replicate_origin": {"type": bool, "default": True},
}


class DBExtenderConnector(DBHandler):
    """
    Extend a DBConnector into another

    The purpose is to solve the following issue.
    You have an external DB (the origin) and you want to add fields
    to the Item from this DB. You can do that with DBExtenderConnector

    """

    @validation_parameters
    def __init__(
        self,
        db_name: str,
        origin_db_handler: DBHandler,
        replicate_db_handler: DBHandler,
        **kwargs,
    ):
        """


        :param db_name: A name for the DB
        :type db_name: str
        :param origin_db_handler: The origin database
        :type origin_db_handler: DBHandler
        :param replicate_db_handler: the local replcate
        :type replicate_db_handler: DBHandler

        :param kwargs: arguments as kwargs for the extender
        :type kwargs: object

        :keyword local: list of path in the Item which are extentions of the origin Item
        :type local: list[ str ]

        :keyword replicate_origin: if you want to replicate localy the origin database
        :type replicate_origin: bool

        :keyword sync_origin: to say if you want to update the origin database
        :type sync_origin: bool


        """

        self._origin_db_handler = origin_db_handler
        self._replicate_db_handler = replicate_db_handler

        # Transformers
        self.transformers: dict[str, dict[str, Transformer]] = {}
        self.type_transformers: dict[str, Transformer] = {}

        options = Kparse(kwargs, KPARSE_MODEL)
        self.list_of_locals: list[str] = options.get("local")

        self.list_of_locals_selectors: list[Selector] = []
        for sel_string in self.list_of_locals:
            self.list_of_locals_selectors.append(Selector(sel_string))

        self._expire: timedelta = options.get("expire")
        self._sync_origin: bool = options.get("sync_origin")
        self._replicate_origin: bool = options.get("replicate_origin")

        self._item_origin = None
        self._item_replica = None

        super().__init__(db_name, **kwargs)

    def set_model(self, item_model) -> None:
        """
        Set the model, but change the model
        for each sub DBHandlers, by adding

        :param model: the Item model
        :type model: Item
        """
        super().set_model(item_model)

        # change the model for each
        self._item_origin = item_model.copy()
        self._item_replica = item_model.copy()

        log.debug(f"List of keys = {item_model.keys()}")
        log.debug(f"List of keys = {item_model.keys()}")

        _id_model = item_model.get_my_model("$._id")
        # Il not local_copy, remove keys except local
        if not self._replicate_origin:
            for key in item_model.keys():
                log.debug(f"Remove {key} on local model")
                self._item_replica.remove_model(key)

        for path_local in self.list_of_locals:
            model = item_model.get_my_model(path_local)
            log.debug(f"Remove path {path_local} on remote model")
            self._item_origin.remove_from_model(path_local)
            log.debug(f"Add path {path_local} on local model")
            self._item_replica.add_to_model(path_local, model)

        log.debug("Add _origin_id and _expire on local model")
        self._item_replica.add_model("_origin_id", String())
        self._item_replica.add_model("_expire", Datetime())
        # _id must be at the end
        self._item_replica.add_model("_id", _id_model)

        self._origin_db_handler.set_model(self._item_origin)
        self._replicate_db_handler.set_model(self._item_replica)

    def check_structure(self, update_directly=False) -> tuple[bool, str]:
        """

        Check if the internal structure is compliant to the model


        :param _update_directly: do the update automatically, defaults to False
        :type _update_directly: bool, optional
        :return: True if compliant, or False, and a message with things to do to be compliant
        :rtype: tuple [ bool, str ]
        """

        res_remote, _mess_remote = self._origin_db_handler.check_structure(
            update_directly
        )
        res_local, _mess_local = self._replicate_db_handler.check_structure(
            update_directly
        )

        mess = f"# Remote DBHandler :\r\n# --------------\r\n{_mess_remote}\r\n# Local DBHandler :\r\n# --------------\r\n{_mess_local}"
        log.debug(f"check structure return :\r\n{mess}")
        return (res_remote & res_local, mess)

    def drop(self) -> None:  # pylint: disable=unused-argument
        """Drop the collection

        Mainly used in test


        :raise Error: Raise an error DBError or any db error
        """
        self._replicate_db_handler.drop()
        if self._sync_origin:
            self._origin_db_handler.drop()

    def connect(self):
        """Try to make a connection to the mongodb

        :raise BDError: Raise an error in case of database Error

        """
        self._origin_db_handler.connect()
        self._replicate_db_handler.connect()

    def close(self):
        """Close the mongodb connection

        :raise DBError: Raise an error in case of database Error

        """
        self._origin_db_handler.close()
        self._replicate_db_handler.close()

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        Mainly, not used, because the database itself do the job (like mongo).
        But for other cases, you must generate by yourself the uniq *_id* for the object

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        return self._replicate_db_handler.generate_id()

    def _has_expired(self, t: datetime | None) -> bool:
        """
        check if has expired

        :param t: _description_
        :type t: datetime
        :return: _description_
        :rtype: bool
        """
        if t is None:
            return False
        if self._expire is None:
            return False
        return datetime.now() + self._expire < t

    def _get_expire_time(self) -> bool:
        """
        get the expiration date

        :param t: _description_
        :type t: datetime
        :return: _description_
        :rtype: bool
        """
        if self._expire is None:
            return None
        return (datetime.now() + self._expire).replace(microsecond=0)

    def get_by_id(self, _id: str) -> dict:  # pylint: disable=unused-argument
        """
        get an object by _id in the DB and return it

        :param _id: the _id
        :type _id: str
        :return: The object (json format)
        :rtype: dict
        :raise Error: Raise an error DBError or any db error

        """
        log.debug(f"local get_by_id({_id})")
        item = self._replicate_db_handler.get_by_id(_id)

        if not item:
            return None

        return self._build_full_object_from_local(item)

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        """Create the object into the DB and return the _id

        :param o: The object given (json format)
        :type o: dict
        :return: The _id of the object.
        :rtype: str

        :raise Error: Raise an error DBError or any db error

        """
        if self._sync_origin is False:
            o["_origin_id"] = None
            o["_expire"] = None
            log.debug(f"local create({o})")
            return self._replicate_db_handler.create(o)

        remote_object = deepcopy(o)
        local_object = {}
        if self._replicate_origin:
            local_object = deepcopy(o)

        for path in self.list_of_locals_selectors:
            pslash = path.to_slash_path()
            ppath = path.to_json_path()
            patch.apply([{"op": "remove", "path": pslash}], remote_object)
            if self._replicate_origin is False:
                a = findall(ppath, o)
                patch.apply(
                    [{"op": "add", "path": pslash, "value": a[0]}], local_object
                )

        if self._sync_origin:
            _id = self._origin_db_handler.create(remote_object)
            local_object["_origin_id"] = _id
            local_object["_expire"] = self._get_expire_time()

        log.debug(f"local create({local_object})")
        return self._replicate_db_handler.create(local_object)

    def save(self, _id: str, o: dict) -> None:  # pylint: disable=unused-argument
        """Save the objet

        :param _id: the _id of this object
        :type _id: str

        :param o: The object given (json format)
        :type o: dict

        :raise Error: Raise an error DBError or any db error

        """

        remote_object = deepcopy(o)
        local_object = {}
        if self._replicate_origin:
            local_object = deepcopy(o)

        for path in self.list_of_locals_selectors:
            pslash = path.to_slash_path()
            ppath = path.to_json_path()
            patch.apply([{"op": "remove", "path": pslash}], remote_object)
            if self._replicate_origin is False:
                a = findall(ppath, o)
                patch.apply(
                    [{"op": "add", "path": pslash, "value": a[0]}], local_object
                )

        if self._sync_origin:
            item = self._replicate_db_handler.get_by_id(_id)
            _origin_id = item.get("_origin_id")
            if not _origin_id:
                raise DBError("{0}.save() : _id {1} has no origin_id", self._name, _id)

            log.debug(f"remote save({_origin_id})")
            self._origin_db_handler.save(_origin_id, remote_object)
            local_object["_origin_id"] = _origin_id
            local_object["_expire"] = self._get_expire_time()

        log.debug(f"local save({_id})")
        self._replicate_db_handler.save(_id, local_object)

    def _merge(self, local_o: dict, remote_o: dict) -> dict:
        """
        Lerge the local and the remote object

        :param local_o: the local
        :type local_o: dict
        :param remote_o: the remote
        :type remote_o: dict
        :return: merged object
        :rtype: dict
        """
        o = remote_o | local_o
        del o["_origin_id"]
        if "_expire" in o:
            del o["_expire"]
        return o

    def _build_full_object_from_remote(self, o: dict) -> dict | None:
        """
        Adapt the _local database with the object get from the remote

        :param o: the object get from the remote DB
        :type o: dict
        """
        origin_id = o.get("_id")

        if not origin_id:
            return None

        resp = self._replicate_db_handler.select(
            SFilter("$._origin_id", Operator.EQ, origin_id)
        )

        local_object = None
        if resp.items is not None:
            for local_o in resp.items:
                if local_o.get("_origin_id") == origin_id:
                    local_object = local_o
                    break

        # A new one in the DB - do a creation
        if not local_object:
            log.debug(f"not found origin for {origin_id}")
            a = self._item_replica.copy()
            a._origin_id = origin_id
            a._expire = self._get_expire_time()
            dict_to_save = a.get_view("save").get_encoded()
            output = dict_to_save | o
            if self._replicate_origin:
                dict_to_save = dict_to_save | o
            log.debug(f"local create({dict_to_save})")
            output["_id"] = self._replicate_db_handler.create(dict_to_save)

            del output["_origin_id"]
            del output["_expire"]
            return output

        # already exists in the DB
        log.debug(f"found origin for {origin_id} = {local_object}")
        # re-check the list (in cas of no filter in the DBHahdler)
        if self._has_expired(local_object):
            o["_expire"] = self._get_expire_time()
            local_object.update(o)
            log.debug(f'local save({local_object["_id"]})')
            self._replicate_db_handler.save(local_object["_id"], local_object)
            del local_object["_origin_id"]
            del local_object["_expire"]
        return local_object

    def _build_full_object_from_local(
        self, o: dict, remote_o: dict = None
    ) -> dict | None:
        """
        Adapt the _local database with the object get from the remote

        :param o: the object get from the remote DB
        :type o: dict
        :param remote_o: the remote object if nedded
        :type remote_o: dict
        """
        _origin_id = o.get("_origin_id")
        expire = o.get("_expire")
        item = o
        must_reload = False
        if self._replicate_origin is False or self._has_expired(expire):
            must_reload = True

        if _origin_id and must_reload:
            item1 = (
                remote_o if remote_o else self._origin_db_handler.get_by_id(_origin_id)
            )
            item = item1 | o

            if item1 and self._replicate_origin and self._has_expired(expire):
                item["_expire"] = self._get_expire_time()
                log.debug(f'local save({o["_id"]})')
                self._replicate_db_handler.save(o["_id"], item)

        if "_origin_id" in item:
            del item["_origin_id"]

        if "_expire" in item:
            del item["_expire"]
        return item

    def _update_local(self, local_o: dict, remote_o: dict) -> str | None:
        """
        update the local with the remote

        :param remote_o: _description_
        :type remote_o: dict
        :return: the _id
        :rtype: str
        """

        if remote_o is None:
            return None

        origin_id = remote_o.get("_id")
        log.debug(f"local _update_local({origin_id})")

        # update the local (if copy or expired)
        if local_o is not None:
            expire = local_o.get("_expire")
            _id = local_o.get("_id")
            if self._replicate_origin and self._has_expired(expire):
                log.debug(f"update local {_id} with remote {_id}")
                new_local = local_o | remote_o
                new_local["_id"] = _id
                new_local["_origin_id"] = origin_id
                new_local["_expire"] = self._get_expire_time()
                self._replicate_db_handler.save(_id, new_local)
            return _id

        # create localy
        new_item = self._item_replica.copy()
        new_item._origin_id = origin_id
        new_item._expire = self._get_expire_time()
        dict_to_save = new_item.get_view("save").get_encoded()
        if self._replicate_origin:
            dict_to_save = dict_to_save | remote_o

        dict_to_save["_origin_id"] = origin_id

        if "_id" in dict_to_save:
            del dict_to_save["_id"]

        log.debug(f"Create local with remote {dict_to_save}")
        return self._replicate_db_handler.create(dict_to_save)

    def delete_by_id(self, _id: str) -> None:
        """The _id to delete on the db

        :param _id: the _id
        :type _id: str
        :raise Error: Raise an error DBError or any db error
        """

        log.debug(f"delete_by_id {_id}")

        if self._sync_origin:
            log.debug(f"local get_by_id {_id}")
            item2 = self._replicate_db_handler.get_by_id(_id)
            _origin_id = item2.get("_origin_id")
            if _origin_id:
                log.debug(f"remote delete_by_id {_origin_id}")
                self._origin_db_handler.delete_by_id(_origin_id)

        log.debug(f"local delete_by_id {_id}")
        return self._replicate_db_handler.delete_by_id(_id)

    def _adapt_filter_to_model(
        self,
        sf: SFilter,
        model,
        replacement_filter: SFilter = SFilter(None, Operator.IGNORE, None),
    ) -> None:
        """
        Adapt the filter to the model
        if the sf._path doesnt exists in the model, replace
        the Sfilter by a Operator.TRUE
        """
        if sf is None:
            return

        if sf._path is None and sf._operator in [Operator.AND, Operator.OR]:
            for sub in sf._value:
                self._adapt_filter_to_model(sub, model)
            return

        if sf._path is None:
            return

        # The _path has no model, modify to set to True
        if model.get_my_model(sf._path) is None:
            log.debug(f"{sf._path} not found in model")
            sf._path = replacement_filter._path
            sf._operator = replacement_filter._operator
            sf._value = replacement_filter._value

    def select(  # pylint: disable=unused-argument
        self,
        select_filter: SFilter = None,
        projection: list[str] = None,
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: Sort = None,
    ) -> SelectResponse:
        """
        Select from filter in the DB and return a list of dicts, with pagination

        :param select_filter: The filter for selection (depends on DB types)
        :param projection: The list of elements we want for each object
        :type projection: dict
        :param page_size: number of elements per page
        :type page_size: int
        :param num_of_element_to_skip: number of element to skip from beginning
        :type num_of_element_to_skip: int
        :param sort_object: Soon
        :type sort_object: dict
        :raise Error: Raise an error DBError or any db error

        """

        response = SelectResponse(page_size, num_of_element_to_skip)

        # First get all remote and add them
        sf1 = deepcopy(select_filter)
        self._adapt_filter_to_model(sf1, self._item_origin)
        if sf1:
            sf1 = sf1.reduce()
        response_remote = self._origin_db_handler.select(
            sf1, None, page_size, num_of_element_to_skip, sort_object
        )
        log.debug(
            f"(remote) sf={sf1} {response_remote.more_than_filter} -> {len(response_remote.items)}"
        )

        # update localy from remote objects
        # if needed
        # ---------------------------------
        remote_items_by_id = {}
        origin_filter = SFilter(None, Operator.OR, [])
        for remote_o in response_remote.items:
            origin_id = remote_o["_id"]
            origin_filter._value.append(SFilter("$._origin_id", Operator.EQ, origin_id))
            remote_items_by_id[origin_id] = remote_o

        if origin_filter:
            origin_filter = origin_filter.reduce()
        response_local = self._replicate_db_handler.select(origin_filter)
        log.debug(
            f"(local update) sf={origin_filter.reduce()} {response_local.more_than_filter} -> {len(response_local.items)} -> {response_local.items}"
        )
        exist_locally = {}
        for local_o in response_local.items:
            origin_id = local_o.get("_origin_id")

            log.debug(f"get localy {origin_id}")

            if origin_id in remote_items_by_id:
                exist_locally[origin_id] = True
                remote_o = remote_items_by_id[origin_id]
                log.debug(f"update localy {origin_id}")
                _id = self._update_local(local_o, remote_o)

        #
        # Create locally
        # --------------
        for remote_o in response_remote.items:
            origin_id = remote_o["_id"]
            if origin_id not in exist_locally:
                log.debug(f"create localy {origin_id} {remote_o}")
                _id = self._update_local(None, remote_o)

        #
        # Select localy for local part of the SFilter
        # -------------------------------------------
        sf2 = deepcopy(select_filter)
        self._adapt_filter_to_model(sf2, self._item_replica, origin_filter)
        if sf2:
            sf2 = sf2.reduce()
        response2 = self._replicate_db_handler.select(
            sf2, projection, page_size, num_of_element_to_skip, sort_object
        )
        log.debug(
            f"(local) sf={sf2} {response2.more_than_filter} -> {len(response2.items)}"
        )

        for local_o in response2.items:
            origin_id = local_o.get("_origin_id")
            # if origin_id in remote_items_by_id:
            response.items.append(
                self._build_full_object_from_local(
                    local_o, remote_items_by_id.get(origin_id)
                )
            )

        response.more_than_filter = (
            response_remote.more_than_filter | response2.more_than_filter
        )
        log.debug(
            f"responses {response.more_than_filter} = {response_remote.more_than_filter} & {response2.more_than_filter}"
        )

        return response
