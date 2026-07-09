"""
Ref and RefsLink strategies
"""

from enum import Enum, auto

class DeleteStrategy(Enum):
    """
    Specifics strategy for deletion for :py:class:`RefsList`

    when the user want to delete the object, if the object contains a :py:class:`RefsList`. Say how to handle the deletion

        - ``MUST_BE_EMPTY`` = The RefsList must be empty otherwise the delete action will raise an error.
        - ``DELETE_REFERENCED_ITEMS`` = All objects targeted with this RefsList will be deleted too. Caution !
        - ``UNLINK_REFERENCED_ITEMS`` = The reverse field of all objects targeted with this RefsList will be cleaned

    """

    MUST_BE_EMPTY = auto()
    DELETE_REFERENCED_ITEMS = auto()
    UNLINK_REFERENCED_ITEMS = auto()

    def __repr__(self):
        return self.name


class FillStrategy(Enum):
    """
    Specifics strategy for fill RefsList in case of one_to_many or many_to_many links

    - ``FILL`` = The reverse is a List of _ids. Usefull to manage which is pointing to me.
    - ``NOT_FILL`` = Whe don't want to fill because the list is to big (for example person -> nationality) but is important to keep the information of this link.

    """

    FILL = auto()  # The default
    NOT_FILL = auto()

    def __repr__(self):
        return self.name
