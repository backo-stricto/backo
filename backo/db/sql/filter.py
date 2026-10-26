# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
filter for sqlite3 db connector
"""

import re
from typing import Callable, Any


from stricto import SFilter, Operator
from ..generic.filter import Filter, FilterReport
from ..generic.transformer import Transformer
from ...error import DBError
from ...sort import Sort, SortItem


class SQlFilter(Filter):
    """
    Filtering for SQL

    """

    def __init__(self, main_table_name: str, get_transformer: Callable):
        """

        :param main_table_name: The main table
        :type main_table_name: str
        :param get_transformer: the function to retrieve :py:class:`Transformer`
        :type get_transformer: Callable
        """

        self._main_table_name = main_table_name
        self.values = []
        self.joins = []
        super().__init__(get_transformer)

    def _equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.EQ return"""
        values.append(str(val))
        return (f"( {field_name} == ?)", FilterReport.EXACT)

    def _greater_than(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.GT return"""
        values.append(str(val))
        return (f"( {field_name} > ?)", FilterReport.EXACT)

    def _greatere_than_equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.GT return"""
        values.append(str(val))
        return (f"( {field_name} >= ?)", FilterReport.EXACT)

    def _less_than(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.GT return"""
        values.append(str(val))
        return (f"( {field_name} < ?)", FilterReport.EXACT)

    def _less_than_equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.LTE return"""
        values.append(str(val))
        return (f"( {field_name} <= ?)", FilterReport.EXACT)

    def _not_equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.NE return"""
        values.append(str(val))
        return (f"( {field_name} != ?)", FilterReport.EXACT)

    def _always_true(self, _field_name: str, _val: Any, values: list[Any]) -> str:
        """Operator.TRUE return"""
        values.append(1)
        return ("( 1 == ? )", FilterReport.EXACT)

    def _always_true_more(self, _field_name: str, _val: Any, values: list[Any]) -> str:
        """Operator.TRUE return"""
        values.append(1)
        return ("( 1 == ? )", FilterReport.MORE)

    def _regexp(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.REG return"""
        values.append(str(val))
        return (f"( {field_name} GLOB ?)", FilterReport.EXACT)

    def _sfilter_to_db_filter(  # pylint: disable=too-many-return-statements, too-many-branches, too-many-statements
        self, sf: SFilter, values: list[Any]
    ) -> tuple[str, FilterReport]:
        """

        Transform a SFilter to a where condition

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """

        if sf._operator == Operator.AND:
            sub_list = []
            filter_report = FilterReport.EXACT
            for sub in sf._value:
                sql_filter, sub_filter_report = self._sfilter_to_db_filter(sub, values)
                sub_list.append(sql_filter)

                if sub_filter_report == FilterReport.MORE:
                    filter_report = FilterReport.LESS
                if sub_filter_report == FilterReport.LESS:
                    filter_report = FilterReport.MORE

            return (f'( {" AND ".join( sub_list ) } )', filter_report)

        if sf._operator == Operator.OR:
            sub_list = []
            filter_report = FilterReport.EXACT
            for sub in sf._value:
                sql_filter, sub_filter_report = self._sfilter_to_db_filter(sub, values)
                sub_list.append(sql_filter)

                if sub_filter_report == FilterReport.MORE:
                    filter_report = FilterReport.LESS
                if sub_filter_report == FilterReport.LESS:
                    filter_report = FilterReport.MORE

            return (f'( {" OR ".join( sub_list ) } )', filter_report)

        if sf._operator == Operator.NOT:
            sql_filter, sub_filter_report = self._sfilter_to_db_filter(
                sf._value, values
            )

            filter_report = FilterReport.EXACT
            if sub_filter_report == FilterReport.MORE:
                filter_report = FilterReport.LESS
            if sub_filter_report == FilterReport.LESS:
                filter_report = FilterReport.MORE

            return (f"( NOT ( {sql_filter} ) )", filter_report)

        if sf._operator == Operator.TRUE:
            return self._always_true(None, None, values)

        if not sf._path:
            raise DBError("Cannot interpret empty filter {0}", repr(sf))

        db_path = sf._path
        db_path = []
        m = sf._path
        m = re.sub(r"^\$\.", "", m)
        db_path = m.split(".")

        model_for_this_path = self._get_model_by_path(
            sf._path, db_path.copy(), self.model
        )

        val = sf._value
        transformer: Transformer = self.get_transformer(db_path)
        if transformer:
            db_path = transformer.get_db_path(db_path)
            val = transformer.transform_filter_value(sf._value)

        table_field_name = f"{self._main_table_name}.{'_'.join(db_path)}"

        if not self._check_operator_compatibility(
            model_for_this_path["types"], sf._operator
        ):
            raise DBError("Cannot do a {0} on {1}", sf._operator, sf._path)

        if sf._operator == Operator.EQ:
            return self._equal(table_field_name, val, values)

        if sf._operator == Operator.GT:
            return self._greater_than(table_field_name, val, values)

        if sf._operator == Operator.GTE:
            return self._greatere_than_equal(table_field_name, val, values)

        if sf._operator == Operator.LTE:
            return self._less_than_equal(table_field_name, val, values)

        if sf._operator == Operator.LT:
            return self._less_than(table_field_name, val, values)

        if sf._operator == Operator.NE:
            return self._not_equal(table_field_name, val, values)

        if sf._operator == Operator.REG:
            return self._regexp(table_field_name, val, values)

        return self._always_true_more(None, None, values)

    def build_db_filter(
        self, backo_filter: SFilter
    ) -> tuple[tuple[str, tuple[str]], FilterReport]:
        """

        Transform a SFilter to a sqlite query

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """
        values = []
        if not backo_filter:
            s, f_report = self._always_true(None, None, values)
            return ((s, values), f_report)

        where_conditions, filter_report = self._sfilter_to_db_filter(
            backo_filter, values
        )
        return ((where_conditions, tuple(values)), filter_report)

    def _sort_to_sort_expression(self, sort_item: SortItem) -> str:
        """
        Transform the sortItem into a string available for order by

        :param sort_item: the sortItem
        :type sort_item: SortItem
        :return: an order by available expression
        :rtype: str
        """

        db_path = sort_item.path
        db_path = []
        m = sort_item.path
        m = re.sub(r"^\$\.", "", m)
        db_path = m.split(".")

        transformer: Transformer = self.get_transformer(db_path)
        if transformer:
            db_path = transformer.get_db_path(db_path)

        table_field_name = f"{self._main_table_name}.{'_'.join(db_path)}"
        return f"{table_field_name} {'ASC' if sort_item.ascendant_order else 'DESC'}"

    def build_db_sort(self, sort: Sort) -> str:
        """
        Transfor the sort into a string "ORDER BY ..."

        :param sort: the sort object
        :type sort: Sort
        :return: the order by string
        :rtype: str
        """

        if sort is None:
            return None

        sorted_expression = []
        for sort_item in sort.list_of_sort_item:
            e = self._sort_to_sort_expression(sort_item)
            if e:
                sorted_expression.append(e)

        return f'ORDER BY {", ".join( sorted_expression )}'
