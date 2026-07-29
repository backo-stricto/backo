# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Item mapper for sqlite3 db connector
"""

from stricto import SFilter, Operator

from ...item_mapper import ItemMapper



class Sqlite3ItemMapper(ItemMapper):
    """
    Specific Sqlite3 Item mapper
    (usee to transform SFilter to Sqlite3 query)
    """


    def set_model( shema: dict )-> None;


    def _sfilter_to_sql_query(  # pylint: disable=too-many-return-statements, too-many-branches
        self, sf: SFilter
    ) -> dict:
        """

        Transform a SFilter to a mongo query

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """

        db_path = sf._path
        if db_path is not None:
            attribute_mapper = self._sfilter_to_sql_query(sf._path)
            if attribute_mapper:
                db_path = attribute_mapper.get_for_filter(sf._path)

        if sf._operator == Operator.AND:
            q = {}
            sub_list = []
            for sub in sf._value:
                sub_list.append(self._sfilter_to_sql_query(sub))

            q["$and"] = sub_list
            return q

        if sf._operator == Operator.OR:
            q = {}
            sub_list = []
            for sub in sf._value:
                sub_list.append(self._sfilter_to_sql_query(sub))

            q["$or"] = sub_list
            return q

        if sf._operator == Operator.NOT:
            q = {}
            q["$not"] = self._sfilter_to_sql_query(sf._value)
            return q

        if sf._operator == Operator.EQ:
            q = {}
            q[db_path] = sf._value
            return q

        if sf._operator == Operator.GT:
            q = {}
            q[db_path] = {"$gt": sf._value}
            return q

        if sf._operator == Operator.GTE:
            q = {}
            q[db_path] = {"$gte": sf._value}
            return q

        if sf._operator == Operator.LTE:
            q = {}
            q[db_path] = {"$lte": sf._value}
            return q

        if sf._operator == Operator.LT:
            q = {}
            q[db_path] = {"$lt": sf._value}
            return q

        if sf._operator == Operator.NE:
            q = {}
            q[db_path] = {"$ne": sf._value}
            return q

        if sf._operator == Operator.REG:
            q = {}
            q[db_path] = {"$regex": sf._value}
            return q

        if sf._operator == Operator.SIZE:
            q = {}
            q[db_path] = {"$size": sf._value}
            return q

        # Not implemented
        return None


