# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
filter for postgres db connector
"""

from typing import Any
from ..sql.filter import SQlFilter
from ..generic.filter import FilterReport


class PostgresFilter(SQlFilter):
    """
    Filtering for postgres

    """

    def _equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.EQ return"""
        values.append(str(val))
        return (f"( {field_name} = %s)", FilterReport.EXACT)

    def _greater_than(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.GT return"""
        values.append(str(val))
        return (f"( {field_name} > %s)", FilterReport.EXACT)

    def _greatere_than_equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.GT return"""
        values.append(str(val))
        return (f"( {field_name} >= %s)", FilterReport.EXACT)

    def _less_than(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.GT return"""
        values.append(str(val))
        return (f"( {field_name} < %s)", FilterReport.EXACT)

    def _less_than_equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.LTE return"""
        values.append(str(val))
        return (f"( {field_name} <= %s)", FilterReport.EXACT)

    def _not_equal(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.NE return"""
        values.append(str(val))
        return (f"( {field_name} != %s)", FilterReport.EXACT)

    def _always_true(self, _field_name: str, _val: Any, _values: list[Any]) -> str:
        """Operator.TRUE return"""
        return ("( true )", FilterReport.EXACT)

    def _always_true_more(self, _field_name: str, _val: Any, _values: list[Any]) -> str:
        """Operator.TRUE return"""
        return ("( True )", FilterReport.MORE)

    def _regexp(self, field_name: str, val: Any, values: list[Any]) -> str:
        """Operator.REG return"""
        values.append(str(val))
        return (f"( {field_name} ~ %s)", FilterReport.EXACT)
