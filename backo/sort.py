"""
Module providing the Sort Class
"""

import re


class SortItem:  # pylint: disable=too-few-public-methods
    """
    Specifics a Sort Item
    """

    path: str
    """ The path for the order"""

    ascendant_order: bool

    def __init__(self, path: str, ascendant_order: bool = True):
        """

        :param path: the path
        :type path: str
        :param ascendant_order: if the sort is ascendant, defaults to True
        :type ascendant_order: bool, optional
        """
        self.path = path
        self.ascendant_order = ascendant_order

    def __repr__(self):
        return f'{"+" if self.ascendant_order else "-"}{self.path}'


class Sort:
    """
    A sort
    """

    list_of_sort_item: list[SortItem]
    """ List of sort Item """

    def __init__(self, sort_as_string: str):
        """ """
        self.list_of_sort_item = []
        if sort_as_string:
            slist = re.split(r"\s*,\s*", sort_as_string)
            for s in slist:
                match = re.match(r"^([\+\-])(.*)\s*$", s)
                if match:
                    self.list_of_sort_item.append(
                        SortItem(match.group(2), match.group(1) == "+")
                    )
                else:
                    self.list_of_sort_item.append(SortItem(s))

    def __repr__(self):
        a = []
        for i in self.list_of_sort_item:
            a.append(repr(i))
        return f"{self.__class__.__name__}[{','.join( a )}]"

    def add_or_replace(self, sort: SortItem) -> None:
        """
        Add a new sort element

        :param sort: _description_
        :type sort: SortItem
        """

        # Replace
        for idx, s in enumerate(self.list_of_sort_item):
            if s.path == sort.path:
                self.list_of_sort_item[idx] = sort
                return

        # Add
        self.list_of_sort_item.append(sort)
