"""
The Collection module
"""

import copy
import sys
from typing import Callable

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    Permissions,
    SRightError,
    SSyntaxError,
    Kparse,
    SFilter,
    Operator,
    validation_parameters,
    get_content,
)

from .db.generic.interface import SelectResponse

from .collection_addon import CollectionAddon
from .log import log_system
from .error import DBError
from .item import Item

log = log_system.get_or_create_logger("select")

KPARSE_MODEL = {
    "can_read|read": {"type": bool | Callable, "default": True},
    "filter": {
        "type": Callable | SFilter,
        "default": SFilter(None, Operator.TRUE, None),
    },
}


class Selection(CollectionAddon):
    """
    The Selection refer to a select on a "table"

    A collection must by registered into a :py:class:`Collection` with :func:`Collection.register_selection`


    .. code-block:: python

        from backo import Item, Collection, Selection

        # example
        book_item = Item({
            "title": String(),
            "subtitle": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })

        database_for_books = DBMongoConnector( "mongodb://localhost:27017/bookcase" , "books" )
        books = Collection( "books", book_item, database_for_books )

        fb = Selection( [ "$.title", "$.subtitle" ], filter={ "$.author.nationality.a2" : "FR" } )
        books.register_selection("french_book", fb )

        nfb = Selection( [ "$.title", "$.subtitle" ], filter={ "$.author.nationality.a2" : ( "$ne", "FR" ) } )
        books.register_selection("non_french_book", nfb )

        # ...


    """

    batch_size: int = 100
    """The best page size for this collection"""

    @validation_parameters
    def __init__(self, selectors: list[str] | None = None, **kwargs):
        """
        :param ``**kwargs``:
        - *filter=* ``SFilter|Callable`` -- the filter whe want to apply for this selection, or a function wich return a SFilter. See stricto for details
        - *can_read=* ``bool|Callable`` -- Wo can do the selection.

        """
        options = Kparse(kwargs, KPARSE_MODEL)

        self._selectors = selectors
        if self._selectors is not None and "$._id" not in self._selectors:
            self._selectors.insert(0, "$._id")

        # Get the filter in SFilter format
        self._filter = options.get("filter")

        # self._db_filter = options.get("db_filter")

        CollectionAddon.__init__(self)
        self._permissions = Permissions(**kwargs)
        self._permissions.add_or_modify_permission("read", options.get("can_read"))

    def get_schema(self) -> dict:
        """
        Return schema for this selection

        :param self: Description
        :return: the schema as a json object (dict)
        :rtype: dict

        Return the schema for this selection
        """
        a = CollectionAddon.get_schema(self)
        a["selectors"] = get_content(self._selectors)

        return a

    def can_read(self) -> bool:
        """
        return True if permission to read
        """
        return self.is_allowed_to("read")

    def _merge_and_filter(self, f1: dict, f2: dict) -> dict:
        """Merge 2 object in a sens of a filter


        :param f1: filter1
        :type f1: dict
        :param f2: filter2
        :type f2: dict
        :return: a new dict with is the merge of f1 and f2
        :rtype: dict
        """
        f = copy.copy(f1) if f1 is not None else {}

        if not isinstance(f2, dict):
            return f

        for key, value in f2.items():
            if key not in f:
                f[key] = copy.copy(value)
                continue
            if isinstance(f[key], dict):
                if isinstance(value, dict):
                    f[key] = self._merge_and_filter(f[key], value)
                    continue
            f[key] = ("$and", [f[key], value])

        return f

    def _set_object(self, obj: dict, with_rights: bool = True) -> Item:
        """
        Set the object as a Item

        :param obj: the object as a dict
        :type obj: dict
        :param with_rights: if we want rights, defaults to True
        :type with_rights: bool, optional
        :return: the object as Item
        :rtype: Item
        """
        o: Item = self.collection.new_item()
        if with_rights:
            o.set(obj)
            o.enable_permissions()
        else:
            o.set_value(obj)

        o.set_status_saved()
        return o

    def _fill_response(
        self,
        response: SelectResponse,
        filter_object: SFilter,
        sort_object: list[str],
        with_right: bool = True,
    ) -> None:
        """
        Do some select into the DD by batch (size self.batch_size)

        :param response: The respons to fill with datas
        :type response: SelectResponse
        :param filter_object: The SFilter
        :type filter_object: SFilter
        :param sort_object: the sorting attributes
        :type sort_object: list[str]
        :raises DBError: In cas of DB return someting different from a SelectResponse
        """

        num_of_element_to_skip = 0
        idx_of_available_item = 0

        while True:
            # Do the DB selection without pagination

            resp: SelectResponse = self.collection.db_handler.select(
                filter_object,
                self._selectors,
                self.batch_size,
                num_of_element_to_skip,
                sort_object,
            )
            if not isinstance(resp, SelectResponse):
                raise DBError(
                    'DBHandler does nor return a SelectResponse "{0}"', self.name
                )

            # At the end of elements in the DB
            if not resp.items:
                break

            for obj in resp.items:
                o = self._set_object(obj, with_right)

                # Ignore all elements matched by the refuse filter
                if self.collection._permissions.is_allowed_to("read", o) is not True:
                    continue

                # The DBHandler did not all the selection. Do it by hand
                if resp.more_than_filter is True and filter_object.check(o) is False:
                    continue

                idx_of_available_item += 1
                if idx_of_available_item <= response.num_of_element_to_skip:
                    continue

                # Set the projection
                if self._selectors:
                    a = []
                    for path in self._selectors:
                        a.append(o.select(path))
                    response.items.append(a)
                else:
                    response.items.append(o)
                if response.page_size and len(response.items) >= response.page_size:
                    break

            # get less elements than asked
            if len(resp.items) < self.batch_size:
                break

            # read the next group of elements
            num_of_element_to_skip += self.batch_size

        # The end of the loop
        # Page size not set, the total can be computed
        if not response.page_size:
            response.total = idx_of_available_item

    def _merge_filters(self, select_filter: SFilter) -> SFilter:
        """
        build the filter with filter given and self._filter

        :param select_filter: the given filter
        :type select_filter: SFilter
        :rtype: SFilter
        """
        f = self._filter() if callable(self._filter) else self._filter
        if not isinstance(f, SFilter):
            raise SSyntaxError(
                'select "{0}" filter "{1}" is not type SFilter', self.name, f
            )
        return select_filter.merge_and(f) if select_filter else f

    def select(
        self,
        select_filter: SFilter = None,
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: list[str] = [],
    ) -> dict:
        """
        Do the selection
        """
        if self.collection is None:
            raise SSyntaxError(
                'The selection "{0}" is not registered into a collection. (miss register_selection ?)',
                self.name,
            )

        if self.can_read() is False:
            raise SRightError("Execute {0} selection is forbidden", self.name)

        # build the filter with filter given and self._filter
        filter_object: SFilter = self._merge_filters(select_filter)

        response = SelectResponse(page_size, num_of_element_to_skip)
        self._fill_response(response, filter_object, sort_object)

        return response.get_as_dict()

    def admin_select(self, select_filter: SFilter = None) -> dict:
        """
        Make a select without pagination and without rights on objects.
        Used by :py:class:`Ref` and :py:class:`RefsList` to find reflective datas

        :param select_filter: the filter, defaults to None
        :type select_filter: SFilter, optional
        :return: a dict with response inside
        :rtype: dict
        """
        if self.collection is None:
            raise SSyntaxError(
                'The selection "{0}" is not registered into a collection. (miss register_selection ?)',
                self.name,
            )
        response = SelectResponse(0, 0)
        self._fill_response(response, select_filter, None, False)

        return response.get_as_dict()

    def count(self, select_filter: SFilter = None) -> int:
        """
        Return the total number of items matching the selection

        :param select_filter: the filter, defaults to None
        :type select_filter: SFilter, optional
        :return: _description_
        :rtype: int
        """

        # build the filter with filter given and self._filter
        filter_object: SFilter = self._merge_filters(select_filter)

        response = SelectResponse(0, 0)

        num_of_element_to_skip = 0
        idx_of_available_item = 0

        while True:
            # Do the DB selection without pagination

            resp: SelectResponse = self.collection.db_handler.select(
                filter_object, self._selectors, self.batch_size, num_of_element_to_skip
            )
            if not isinstance(resp, SelectResponse):
                raise DBError(
                    'DBHandler does nor return a SelectResponse "{0}"', self.name
                )

            # At the end of elements in the DB
            if not resp.items:
                break

            for obj in resp.items:
                o = self._set_object(obj)

                # Ignore all elements matched by the refuse filter
                if self.collection._permissions.is_allowed_to("read", o) is not True:
                    continue

                # The DBHandler did not all the selection. Do it by hand
                if resp.more_than_filter is True and filter_object.check(o) is False:
                    continue

                idx_of_available_item += 1
                if idx_of_available_item <= response.num_of_element_to_skip:
                    continue

                if response.page_size and len(response.items) >= response.page_size:
                    break

            # get less elements than asked
            if len(resp.items) < self.batch_size:
                break

            # read the next group of elements
            num_of_element_to_skip += self.batch_size

        return idx_of_available_item
