"""
Interface between backo and DBHandlers
"""


class SelectResponse:
    """
    The response of a select()
    """

    def __init__(self, page_size: int, num_of_element_to_skip: int):

        self.items: list[dict] = []
        self.total: int = None
        self.more_than_filter: bool = True
        self.full_object: bool = True
        self.page_size: int = page_size
        self.num_of_element_to_skip: int = num_of_element_to_skip
        self.sorted: bool = False

    def __repr__(self):
        return f"SR( items:{len(self.items)}, total:{self.total}, more_than_filter:{self.more_than_filter}, full_object:{self.full_object}, num_of_element_to_skip:{self.num_of_element_to_skip}, page_size:{self.page_size} )"

    def __str__(self):
        return repr(self)

    def get_as_dict(self) -> dict:
        """
        Return as a dict (for client side

        :return: values as a dict
        :rtype: dict
        """
        return {
            "result": self.items,
            "total": self.total,
            "_skip": self.num_of_element_to_skip,
            "_page": self.page_size,
        }
