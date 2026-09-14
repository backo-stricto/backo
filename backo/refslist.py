"""
Ref and RefsLink class definition
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import sys
import copy
from typing import Self, TYPE_CHECKING

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    String,
    List,
    Selector,
    SSyntaxError,
    STypeError,
    Kparse,
    SFilter,
    Operator,
)

from .loop_path import LoopPath
from .error import BackoError, NotFoundError, TemporaryNotFound
from .log import log_system

from .refs_strategies import DeleteStrategy, FillStrategy

if TYPE_CHECKING:
    from .collection import Collection
    from .item import Item

# WARNING: Specific import for cycling import beetween Ref and RefsLists
from . import ref

log = log_system.get_or_create_logger("ref")

DEFAULT_ID = "NULL_ID"


REFSLIST_KPARSE_MODEL = {
    "collection|coll*": str,
    "reverse|rev|field": str,
    "require|required": {"type": bool, "default": False},
    "on_delete|ods": {"type": DeleteStrategy, "default": DeleteStrategy.MUST_BE_EMPTY},
    "on_fill|ofs": {"type": FillStrategy, "default": FillStrategy.FILL},
    "on": {"type": list[tuple], "default": []},
}


class RefsList(List):
    """Ref 0 or 1 to many to another :py:class:`Collection`

    :param ``**kwargs``:
        - *collection|coll=* ``str`` -- The target collection
        - *reverse|rev|field=* ``str`` -- The field in the target collection which reference my collection. Must be a RFC 9535 path (https://datatracker.ietf.org/doc/rfc9535/)
        - *on_delete|ods=* :py:class:`DeleteStrategy` -- The deletion strategy :py:class:`DeleteStrategy`. By default =``DeleteStrategy.MUST_BE_EMPTY``

    .. code-block:: python

        from backo import Item, Ref, RefsList, DeleteStrategy

        # example
        book_item = Item({
            "title": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })
        author_item = Item({
            "name": String(),
            "surname": String(),
            "books": RefsList(collection="books", field="$.author", ods=DeleteStrategy.DELETE_REFERENCED_ITEMS),
        })

        books = Collection( "books", book_item, database_for_books )
        authors = Collection( "authors", author_item, database_for_authors )

        my_bookstore = Backoffice("bookstore")
        my_bookstore.register_collection(books)
        my_bookstore.register_collection(authors)


    """

    def __init__(self, **kwargs):
        """Constructor"""

        options = Kparse(kwargs, REFSLIST_KPARSE_MODEL)
        self._collection = options.get("collection")
        self._reverse = options.get("reverse")

        self._require = options.get("require")

        self._coll_ref = None

        # Strategy for fill
        self._fill_strategy = options.get("on_fill")

        # Strategy for deletion and modification
        self._on_delete_strategy = options.get("on_delete")

        on_delete_strategy = on_delete_must_by_empty
        if self._on_delete_strategy == DeleteStrategy.DELETE_REFERENCED_ITEMS:
            on_delete_strategy = on_delete_with_reverse
        if self._on_delete_strategy == DeleteStrategy.UNLINK_REFERENCED_ITEMS:
            on_delete_strategy = on_delete_clean_reverse

        # for events
        on = copy.copy(options.get("on"))
        on.append(("created", on_created))
        on.append(("before_delete", on_delete_strategy))
        on.append(("before_save", on_modify_clean_reverse))
        on.append(("check_syntax", check_syntax))
        on.append(("loaded", on_loaded, "$"))

        List.__init__(
            self, String(default=DEFAULT_ID, required=True), on=on, default=[], **kwargs
        )

    def set_collection_reference(self):
        """Set the reference to the Item object to the collection referenced.

        :meta private:

        """
        # Already set
        if self._coll_ref is not None:
            return

        root1 = self.get_root()._collection
        self._coll_ref = root1.get_other_collection(self._collection)
        if not self._coll_ref:
            raise SSyntaxError(
                'RefsList "{0}" to unnknown collection "{1}"',
                self.path_name(),
                self._collection,
            )
        return

    def get_schema(self) -> dict:
        """get schema for ref with specific elements
        collection and reverse

        :return: the schema
        :rtype: dict
        """
        a = super().get_schema()
        a["collection"] = self._collection
        a["reverse"] = self._reverse
        return a

    def remove_ref(self, _id: str | None) -> bool:
        """
        Remove an _id from the list of _ids
        and return True if something changed

        :param _id: The _id to remove
        :type _id: str | None
        :return: True if some changement
        :rtype: bool
        """
        if _id not in self.get_value():
            return False
        self.remove(_id)
        return True

    def add_ref(self, _id: str | None) -> bool:
        """
        Add a new value = change the value
        and return True if something changed

        :param _id_to_add: the _id to add or None if clear
        :type _id_to_add: str|None
        :return: True if some changement
        :rtype: bool
        """

        # Nothing to do
        if _id in self.get_value():
            return False
        self.append(_id)
        return True

    def check_consistancy(self, **kwargs):  # pylint: disable=unused-argument
        """
        Check the consistancy for thos Ref
        (follow ref and reverse to find lost _ids)
        """
        root = self.get_root()
        log.debug(
            f"{root._collection.name}//{self.path_name()} for id={root._id} check consistancy"
        )

    def get_selectors(self, index_or_slice, sel: Selector):
        """
        rewrite get_selector to populate the sub-object and continue

        :meta private:

        """

        # No need to continue, return self or slice of lists
        if sel.empty():
            if index_or_slice is None:
                return self
            return List.get_selectors(self, index_or_slice, sel)

        # Get all ids depending on index_or_slice
        list_ids_or_id = List.get_selectors(self, index_or_slice, Selector(None))

        if list_ids_or_id is None:
            return None

        # set the _coll_ref (in case of)
        self.set_collection_reference()

        # Continue further with a list of ids
        if isinstance(list_ids_or_id, (RefsList, list, List)):
            a = []
            for other_id in list_ids_or_id:
                other = self._coll_ref.new()
                try:
                    other.load(other_id)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue
                result = other.get_selectors(None, sel.copy())
                if result is not None:
                    a.append(result)
            return a

        # Continue further with a uniq id
        other = self._coll_ref.new()
        try:
            other.load(list_ids_or_id)
        except Exception:  # pylint: disable=broad-exception-caught
            return None
        return other.get_selectors(None, sel)

    def get_reverse(self) -> ref.Ref | Self:
        """
        Return the reverse field

        :return: _description_
        :rtype: Ref|refslist.RefsList
        """

        if not self._reverse:
            return None

        # set the _coll_ref (in case of)
        self.set_collection_reference()

        # check if need to fill the reverse or not
        reverse_field_model = self._coll_ref.model.select(self._reverse)

        if reverse_field_model is None:
            raise STypeError(
                "{0}.{1} is doesn't exists", self._collection, self._reverse
            )

        # The reverse is not a ref ?!!!
        if not isinstance(reverse_field_model, (ref.Ref, RefsList)):
            raise STypeError(
                "{0}.{1} is not a Ref or a RefsList", self._collection, self._reverse
            )

        return reverse_field_model

    def load_others(
        self, _ids: list[str], **kwargs
    ) -> list[tuple[Item, ref.Ref | Self]]:
        """
        Load the target object and the reverse field
        """

        reverse_field_model = self.get_reverse()

        # Avoid loops
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs["looper"]

        match_filter = None
        # Set the filter for a select
        # With a Fill Strategy
        # if self._fill_strategy == FillStrategy.FILL:
        if _ids is not None:
            if not _ids:
                return []

            match_filter_list = []
            for _id in _ids:
                if not _id:
                    continue

                if looper.is_loop(self._collection, _id, self._reverse):
                    log.debug(
                        f"Stop following ref due to loop ( {self._collection}, {_id}, {self._reverse})"
                    )
                    continue

                match_filter_list.append(SFilter("$._id", Operator.EQ, _id))

            if match_filter_list:
                match_filter = SFilter(None, Operator.OR, match_filter_list)
        else:
            # With a Not.Fill Strategy
            if reverse_field_model is not None:
                root_id = self.get_root()._id.get_value()
                if isinstance(reverse_field_model, ref.Ref):
                    match_filter = SFilter(self._reverse, Operator.EQ, root_id)
                if isinstance(reverse_field_model, RefsList):
                    match_filter = SFilter(
                        self._reverse,
                        Operator.CONTAINS,
                        SFilter("@", Operator.EQ, root_id),
                    )

        log.debug(f"load_others filter = {match_filter}")
        if not match_filter:
            return []

        others = []
        others = self._coll_ref.admin_select(match_filter)

        response = []
        for other in others:

            if looper.is_loop(self._collection, other._id.get_value(), self._reverse):
                log.debug(
                    f"Stop following ref due to loop ( {self._collection}, {other._id.get_value()}, {self._reverse})"
                )
                continue

            reverse_field = other.select(self._reverse)
            if reverse_field is None:
                log.error(
                    f'Path "{self._reverse}" not found in collection "{self._collection}" for item {other._id.get_value()}'
                )
                continue

            response.append((other, reverse_field))
        return response


def check_syntax(
    event_name: str, root: Item, me: RefsList, **kwargs
):  # pylint: disable=unused-argument
    """
    Check if everything is correct log some warnings
    """
    log.debug(f"Check the syntax {root._collection.name}/{me.path_name()}")
    try:
        me.set_collection_reference()
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    if not me._coll_ref:
        log.error(
            f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}" not found'
        )
        return
    if not me._reverse:
        log.warning(
            f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}". No reverse defined. Are you sure ?'
        )

    else:
        # fill the field
        other = me._coll_ref.new_item()
        reverse_field = other.select(me._reverse)
        if not isinstance(
            reverse_field, (ref.Ref, RefsList)
        ):  # pylint: disable=singleton-comparison
            log.error(
                f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}", "{me._reverse}" is not a Ref or a RefsList'
            )
            return


def on_loaded(
    event_name, root: Item, me: RefsList, **kwargs
):  # pylint: disable=unused-argument
    """Trigged when the Item is loaded from the DB.
    if the fill_strategy is "NO_FILL", do the select from the reverse to fill it
    Args:
        event_name (_type_): _description_
        root (_type_): _description_
        me (_type_): _description_
    """

    if me._fill_strategy == FillStrategy.FILL:
        return

    # No reverse => nothing to do.
    if not me._reverse:
        return

    log.debug(
        f"on_loaded reflist {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    others_with_reverse = me.load_others(None, **kwargs)
    log.debug(f"on_loaded reflist not filled other = {others_with_reverse}")
    me.set_value([])
    for other, _ref_or_refslist in others_with_reverse:
        if other is None:
            continue
        me.add_ref(other._id.get_value())

    log.debug(f"loaded reflist not filled with = {me}")


def on_created(
    event_name: str, root: Item, me: RefsList, **kwargs
):  # pylint: disable=unused-argument
    """
    A creation object with a RefList
    Fill other if
    :meta private:
    """
    if me is None:
        raise SSyntaxError("{0}.{1} 'me' is None", me._collection, me.path_name())
    log.debug(
        "%r/%r created with RefsList %r=%r",
        root._collection.name,
        root._id,
        me.path_name(),
        me,
    )

    reverse_field_model = me.get_reverse()
    if reverse_field_model is None:
        return

    _ids = me.get_value()
    if len(_ids) == 0:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs["looper"]
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_created reflist {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    others_with_reverse = me.load_others(me.get_value(), **kwargs)
    for other, ref_or_refslist in others_with_reverse:
        if other is None:
            continue
        if ref_or_refslist is None:
            continue
        if ref_or_refslist.add_ref(root._id.get_value()):
            other.save(**kwargs)
    return


def on_delete_must_by_empty(
    event_name: str, root: Item, me: RefsList, **kwargs
):  # pylint: disable=unused-argument
    """
    The object will be deleted only if this list is empty
    otherwist error
    :meta private:
    """
    if not isinstance(me, RefsList):
        raise SSyntaxError(
            "{0}.{1} 'me' is not a RefsList (type={2})",
            me._collection,
            me.path_name(),
            type(me),
        )

    # No reverse => nothing to do.
    if not me._reverse:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs["looper"]
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_delete_must_by_empty reflist {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    # With FillStrategy.FILL, just chek if the list is empty
    if me._fill_strategy == FillStrategy.FILL:
        if len(me) == 0:
            return

        # Check of this delete comes from the reverse
        for _id in me:
            if not looper.is_loop(me._collection, _id, me._reverse):
                raise BackoError('Collection "{0}" not empty', me._collection)

    else:
        # FillStrategy.NOT_FILL, mus do a select to find
        # if ther is some ref to me.
        # set the _coll_ref (in case of)
        others_with_reverse = me.load_others(None, **kwargs)
        if len(others_with_reverse) != 0:
            raise BackoError('Collection "{0}" not empty', me._collection)


def on_delete_with_reverse(
    event_name: str, root: Item, me: RefsList, **kwargs
):  # pylint: disable=unused-argument
    """
    The ref object object will be deleted too
    otherwise error
    :meta private:
    """
    if not isinstance(me, RefsList):
        raise SSyntaxError(
            "{0}.{1} 'me' is not a RefsList (type={2})",
            me._collection,
            me.path_name(),
            type(me),
        )

    # No reverse => nothing to do.
    if not me._reverse:
        return

    _ids = me.get_value()
    if len(_ids) == 0 and me._fill_strategy == FillStrategy.FILL:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs["looper"]
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_delete_with_reverse reflist {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    others_with_reverse = me.load_others(_ids, **kwargs)
    log.debug(f"on_delete_with_reverse return others {others_with_reverse}")
    for other, _ref_or_refslist in others_with_reverse:
        if other is None:
            continue
        try:
            other.delete(**kwargs)
        except TemporaryNotFound as e:
            log.warning(
                f"{me.path_name()} : delete {other._id.get_value()} in collection {me._collection} actually not available ({e})"
            )
            continue
        except NotFoundError as e:
            log.info(
                f"{me.path_name()} : delete {other._id.get_value()} in collection {me._collection} not found ({e})"
            )
            continue
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.warning(
                f"{me.path_name()} : delete {other._id.get_value()} in collection {me._collection} return an error ({e})"
            )
            continue
    return


def on_delete_clean_reverse(
    event_name: str, root: Item, me: RefsList, **kwargs
):  # pylint: disable=unused-argument
    """
    The reflecting object is cleaned too
    :meta private:
    """
    if not isinstance(me, RefsList):
        raise SSyntaxError(
            "{0}.{1} 'me' is not a RefsList (type={2})",
            me._collection,
            me.path_name(),
            type(me),
        )

    # No reverse => nothing to do.
    if not me._reverse:
        return

    _ids = me.get_value()
    if len(_ids) == 0:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs["looper"]
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_delete_with_reverse reflist {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    others_with_reverse = me.load_others(me.get_value(), **kwargs)
    log.debug(f"on_delete_clean_reverse {others_with_reverse}")

    for other, ref_or_refslist in others_with_reverse:
        if other is None:
            continue
        if ref_or_refslist is None:
            continue
        if ref_or_refslist.remove_ref(root._id.get_value()):
            other.save(**kwargs)


def on_modify_clean_reverse(  # pylint: disable=too-many-branches
    _event_name: str, root: Item, me: RefsList, **kwargs
):
    """
    The reflecting object is set to the new one
    :meta private:
    """
    if not isinstance(me, RefsList):
        raise SSyntaxError(
            f"{me._collection}.{me.path_name()} 'me' is not a RefsList (type={type(me)}{me.path_name()})"
        )

    # No reverse => nothing to do.
    if not me._reverse:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs["looper"]
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_modify_clean_reverse for {root._collection.name}({root._id.get_value()}) {me.path_name()} = {me.get_value()}"
    )

    # get the olf object
    old = kwargs.get("old_object")
    if old is None:
        return
    # get the previous version of "me" and check if there is a version
    # and different from the new one
    old_me: RefsList = old.select(me.path_name())
    log.debug(f"on_modify_clean_reverse old_me = {old_me.get_value()}")

    _ids_to_remove = []
    _ids_to_add = []
    for _id in me.get_value():
        if _id not in old_me.get_value():
            _ids_to_add.append(_id)
    for _id in old_me.get_value():
        if _id not in me.get_value():
            _ids_to_remove.append(_id)

    # remove
    if _ids_to_remove:
        others_with_reverse = me.load_others(_ids_to_remove, **kwargs)
        log.debug(
            f"on_modify_clean_reverse - others to remove {_ids_to_remove} = {others_with_reverse}"
        )
        for other, ref_or_refslist in others_with_reverse:
            if other is None or ref_or_refslist is None:
                continue
            if ref_or_refslist.remove_ref(root._id.get_value()):
                other.save(**kwargs)
    # add
    if _ids_to_add:
        others_with_reverse = me.load_others(_ids_to_add, **kwargs)
        log.debug(f"on_modify_clean_reverse - others to add = {others_with_reverse}")
        for other, ref_or_refslist in others_with_reverse:
            if other is None or ref_or_refslist is None:
                continue
            if ref_or_refslist.add_ref(root._id.get_value()):
                other.save(**kwargs)
