"""
Ref and RefsLink class definition
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code
from __future__ import annotations
import sys
import copy
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .collection import Collection
    from .item import Item

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    String,
    Selector,
    SSyntaxError,
    STypeError,
    Kparse,
)

from .loop_path import LoopPath
from .log import log_system


from .refs_strategies import FillStrategy

# WARNING: Specific import for cycling import beetween Ref and RefsLists
from . import refslist

log = log_system.get_or_create_logger("ref")

DEFAULT_ID = "NULL_ID"


# pylint: disable=pointless-string-statement
"""
██████╗ ███████╗███████╗
██╔══██╗██╔════╝██╔════╝
██████╔╝█████╗  █████╗
██╔══██╗██╔══╝  ██╔══╝
██║  ██║███████╗██║
╚═╝  ╚═╝╚══════╝╚═╝
A reference to another table
"""


REF_KPARSE_MODEL = {
    "collection|coll*": str,
    "reverse|rev|field": str,
    "require|required": {"type": bool, "default": False},
    # "on_fill|ofs": {"type": FillStrategy, "default": FillStrategy.FILL},
    "on": {"type": list[tuple], "default": []},
}


class Ref(String):  # pylint: disable=too-many-instance-attributes
    """Ref 0 or 1 to many to another :py:class:`Collection`

    :param ``**kwargs``:
        - *collection|coll=* ``str`` -- The target collection
        - *reverse|rev|field=* ``str`` -- The field in the target collection which reference my collection. Must be a RFC 9535 path (https://datatracker.ietf.org/doc/rfc9535/)


    .. code-block:: python

        from backo import Item, Ref, RefsList

        # example
        book_item = Item({
            "title": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })
        author_item = Item({
            "name": String(),
            "surname": String(),
            "books": RefsList(collection="books", field="$.author"),
        })

        books = Collection( "books", book_item, database_for_books )
        authors = Collection( "authors", author_item, database_for_authors )

        my_bookstore = Backoffice("bookstore")
        my_bookstore.register_collection(books)
        my_bookstore.register_collection(authors)

    """

    def __init__(self, **kwargs):
        """Constructor"""

        options = Kparse(kwargs, REF_KPARSE_MODEL)

        self._collection: str = options.get("collection")
        self._reverse: str = options.get("reverse")
        self._coll_ref = None

        # For required
        require = options.get("require")
        default = DEFAULT_ID if require is True else None

        # Strategy for fill
        self._fill_strategy = FillStrategy.FILL  # options.get("on_fill")

        # for events
        on = copy.copy(options.get("on"))
        on.append(("created", on_created, "$"))
        on.append(("before_delete", on_delete, "$"))
        on.append(("before_save", on_before_save, "$"))
        on.append(("check_syntax", check_syntax, "$"))
        on.append(("loaded", on_loaded, "$"))

        String.__init__(
            self,
            default=default,
            required=require,
            on=on,
            **kwargs,
        )

    def set_collection_reference(self):
        """Set the reference to the Item object to the collection referenced.

        :meta private:

        """
        # Already set
        if self._coll_ref is not None:
            return

        my_collection: Collection = self.get_root()._collection
        self._coll_ref = my_collection.get_other_collection(self._collection)
        if not self._coll_ref:
            raise SSyntaxError(
                'Ref "{0}" to unnknown collection "{1}"',
                self.path_name(),
                self._collection,
            )

        return

    def get_reverse(self) -> Ref | refslist.RefsList:
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
        if not isinstance(reverse_field_model, (Ref, refslist.RefsList)):
            raise STypeError(
                "{0}.{1} is not a Ref or a RefsList", self._collection, self._reverse
            )

        return reverse_field_model

    def load_target(self, _id: str, **kwargs) -> tuple[Any, Ref | refslist.RefsList]:
        """
        Load the target object and the reverse field
        """
        # set the _coll_ref (in case of)
        self.set_collection_reference()

        # Avoid loops
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs.get("looper")
        if looper.is_loop(self._collection, _id, self._reverse):
            log.debug(
                f"Stop following ref due to loop ( {self._collection}, {_id}, {self._reverse})"
            )
            return (None, None)

        # try to load the coresponding field
        other = self._coll_ref.new()
        other.load(_id, **kwargs)

        if not self._reverse:
            return (other, None)
        reverse_field = other.select(self._reverse)

        if reverse_field._fill_strategy == FillStrategy.NOT_FILL:
            return (other, None)

        return (other, reverse_field)

    def add_ref(self, _id: str | None) -> bool:
        """
        Add a new value = change the value

        :param _id_to_add: the _id to add or None if clear
        :type _id_to_add: str|None
        """

        # Nothing to do
        if _id == self.get_value():
            return False

        self.set(_id)
        return True

    def remove_ref(self, _id: str | None) -> bool:
        """
        Add a new value = change the value

        :param _id_to_add: the _id to add or None if clear
        :type _id_to_add: str|None
        """

        # Nothing to do
        if not self.get_value():
            return False

        self.set(None)
        return True

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
        # Cannot have index or slice on a Ref
        if index_or_slice:
            return None

        if sel.empty():
            return self

        # Load the other to continue

        # set the _coll_ref (in case of)
        self.set_collection_reference()
        # try to load the coresponding field
        other = self._coll_ref.new()
        try:
            other.load(self.get_value())
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.warning(
                f"{self.path_name()} : load {self.get_value()} in collection {self._collection} return an error ({e})"
            )

        # The index_or_slice is actually ignored.
        # (key, sub_index_or_slice) = sel.pop()

        # continue the selection
        return other.get_selectors(None, sel)

    def get_view(self, view_name, final=True):  # pylint: disable=protected-access
        """
        Return all elements belonging to view_name
        true return is a subset of this Dict

        :meta private:

        """
        return String.get_view(self, view_name, final)


def check_syntax(
    event_name: str, root: Item, me: Ref, **kwargs
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
        # Must check == None rather
        if not isinstance(
            reverse_field, (refslist.RefsList, Ref)
        ):  # pylint: disable=singleton-comparison
            log.error(
                f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}", "{me._reverse}" is not a Ref or a RefsList'
            )
            return
        if (
            me._fill_strategy == FillStrategy.NOT_FILL
            and reverse_field._fill_strategy == FillStrategy.NOT_FILL
        ):
            log.error(
                f'{root._collection.name}/{me.path_name()} and Collection "{me._collection}", "{me._reverse}" are with no_fill strategies !'
            )
            return


def on_loaded(
    event_name, root: Item, me: Ref, **kwargs
):  # pylint: disable=unused-argument
    """Trigged when the Item is loaded from the DB.
    if the fill_strategy is "NO_FILL", do the select from the reverse to fill it
    Args:
        event_name (_type_): _description_
        root (_type_): _description_
        me (_type_): _description_
    """

    log.debug(
        f"on_load {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    if me._fill_strategy == FillStrategy.FILL:
        if me.get_value() == None:
            return
        return

    return


def on_before_save( # pylint: disable=too-many-return-statements
    event_name: str, root: Item, me: Ref, **kwargs
):  # pylint: disable=unused-argument
    """
    Before saving, check if the reference
    as changed from an old value
    :meta private:
    """
    # No reverse => nothing to do.
    if not me._reverse:
        return
    # get the old object. If not, the object is currently creating
    old = kwargs.get("old_object")
    if old is None:
        return
    # get the previous version of "me" and check if there is a version
    # and different from the new one
    old_me = old.select(me.path_name())
    if old_me == me:
        return

    # Check if there is a revers field to handle.
    # If there is no reverse, or the reverse don't need to be filled
    # nothig to do
    reverse_field_model = me.get_reverse()

    if reverse_field_model is None:
        return
    if reverse_field_model._fill_strategy == FillStrategy.NOT_FILL:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs.get("looper")
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_before_save {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    # Remove from old

    if old_me.get_value():
        other, ref_or_refslist = me.load_target(old_me.get_value(), **kwargs)
        if other is None or ref_or_refslist is None:
            return
        if ref_or_refslist.remove_ref(root._id.get_value()):
            other.save(**kwargs)

    # Add the new
    if me.get_value():
        other, ref_or_refslist = me.load_target(me.get_value(), **kwargs)
        if other is None or ref_or_refslist is None:
            return
        if ref_or_refslist.add_ref(root._id.get_value()):
            other.save(**kwargs)


def on_delete(
    event_name: str, root: Item, me: Ref, **kwargs
):  # pylint: disable=unused-argument, too-many-return-statements
    """
    The object will be deleted
    clean structure
    :meta private:
    """
    # No reverse => nothing to do.
    if not me._reverse:
        return
    if me == DEFAULT_ID:
        return
    if me.get_value() is None:
        return

    # Check if there is a revers field to handle.
    # If there is no reverse, or the reverse don't need to be filled
    # nothig to do
    reverse_field_model = me.get_reverse()

    if reverse_field_model is None:
        return
    if reverse_field_model._fill_strategy == FillStrategy.NOT_FILL:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs.get("looper")
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        "on_delete %r/%r %r=%r ", root._collection.name, root._id, me.path_name(), me
    )

    # Remove from old
    other, ref_or_refslist = me.load_target(me.get_value(), **kwargs)
    if other is None:
        return
    if ref_or_refslist is None:
        return
    if ref_or_refslist.remove_ref(root._id.get_value()):
        other.save(**kwargs)


def on_created(
    event_name: str, root: Item, me: Ref, **kwargs
):  # pylint: disable=unused-argument
    """
    The object as been created
    check for the reverse field and modify it
    :meta private:
    """
    # No reverse => nothing to do.
    log.debug(f"Ref on_create {id(me.get_root())} {id(root)} {me.path_name()}")
    if not me._reverse:
        return
    # A created object with no reference set. finish
    target_id = me.get_value()
    log.debug(f"Ref on_create {me.path_name()} {target_id}")
    if target_id is None:
        return

    # Check if there is a revers field to handle.
    # If there is no reverse, or the reverse don't need to be filled
    # nothig to do
    reverse_field_model = me.get_reverse()

    if reverse_field_model is None:
        return
    if reverse_field_model._fill_strategy == FillStrategy.NOT_FILL:
        return

    # Avoid loops
    if "looper" not in kwargs:
        kwargs["looper"] = LoopPath()
    looper: LoopPath = kwargs.get("looper")
    if looper.append_or_loop(
        root._collection.name, root._id.get_value(), me.path_name()
    ):
        log.debug(
            f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
        )
        return

    log.debug(
        f"on_created {me._fill_strategy} {root._collection.name}({root._id})/{me.path_name()} = {me}"
    )

    # Add the new
    other, ref_or_refslist = me.load_target(me.get_value(), **kwargs)
    if other is None or ref_or_refslist is None:
        return
    if ref_or_refslist.add_ref(root._id.get_value()):
        other.save(**kwargs)
