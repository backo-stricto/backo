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
from .pragma import get_sqlite3_type_from_backo


class SQlite3Filter(Filter):
    """
    Filtering for sqlite3

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
            values.append(1)
            return ("( 1 == ? )", FilterReport.EXACT)

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
        sql_type = get_sqlite3_type_from_backo(model_for_this_path["types"])

        val = sf._value
        transformer: Transformer = self.get_transformer(db_path)
        if transformer:
            db_path = transformer.get_db_path(db_path)
            val = transformer.transform_filter_value(sf._value)

        table_field_name = f"{self._main_table_name}.{'_'.join(db_path)}"

        if sf._operator == Operator.EQ:

            values.append(str(val))
            return (f"( {table_field_name} == ?)", FilterReport.EXACT)

        if sf._operator == Operator.GT:
            if sql_type not in ["INTEGER", "REAL", "DATE"]:
                raise DBError("Cannot do a gt on {0}", sf._path)

            values.append(val)
            return (f"( {table_field_name} > ?)", FilterReport.EXACT)

        if sf._operator == Operator.GTE:
            if sql_type not in ["INTEGER", "REAL", "DATE"]:
                raise DBError("Cannot do a gte on {0}", sf._path)

            values.append(str(val))
            return (f"( {table_field_name} >= ?)", FilterReport.EXACT)

        if sf._operator == Operator.LTE:
            if sql_type not in ["INTEGER", "REAL", "DATE"]:
                raise DBError("Cannot do a lte on {0}", sf._path)

            values.append(str(val))
            return (f"( {table_field_name} <= ?)", FilterReport.EXACT)

        if sf._operator == Operator.LT:
            if sql_type not in ["INTEGER", "REAL", "DATE"]:
                raise DBError("Cannot do a lt on {0}", sf._path)

            values.append(str(val))
            return (f"( {table_field_name} < ?)", FilterReport.EXACT)

        if sf._operator == Operator.NE:

            values.append(str(val))
            return (f"( {table_field_name} != ?)", FilterReport.EXACT)

        return ("( 1 == ? )", FilterReport.MORE)

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
        if not backo_filter:
            return (("( 1 == ? )", (1,)), FilterReport.EXACT)

        values = []
        where_conditions, filter_report = self._sfilter_to_db_filter(
            backo_filter, values
        )
        return ((where_conditions, tuple(values)), filter_report)
