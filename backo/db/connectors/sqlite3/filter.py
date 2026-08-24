# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
filter for sqlite3 db connector
"""

import re
from typing import Callable


from stricto import SFilter, Operator
from ...filter import Filter
from ...transformer import Transformer
from ....error import DBError
from .pragma import get_sqlite3_type_from_backo


class SQlite3Filter(Filter):
    """
    Filter transformation for sqlite3

    """

    def __init__(self, main_table_name: str, get_transformer: Callable):

        self._main_table_name = main_table_name
        self.values = []
        self.joins = []
        super().__init__(get_transformer)

    def _get_model_by_path(self, path: str, key_path: list[str], model: dict) -> dict:
        """
        Return the corresponding model to check if the path dont go out of the model

        :param path: the path as string (like '$.address.street' )
        :type path: str
        :param key_path: the path (like [ 'address', 'steet' ])
        :type key_path: list[str]
        :param model: the backo model
        :type model: dict
        :return: the corresponding sub model
        :rtype: dict
        """
        if not key_path:
            return model

        if "sub_scheme" in model:
            sub_model = model["sub_scheme"]
            p = key_path.pop(0)
            if not p in sub_model:
                raise DBError("Wrong path {0} (doesnt exists in model)", path)
            return self._get_model_by_path(path, key_path, sub_model[p])

        if "sub_type" in model:
            raise DBError("Filter in list not implemented (path={0})", path)

        if "sub_types" in model:
            raise DBError("Filter in tuples not implemented (path={0})", path)

        raise DBError("Wrong path {0} (doesnt exists in model)", path)

    def _sfilter_to_db_filter(  # pylint: disable=too-many-return-statements, too-many-branches
        self, sf: SFilter
    ) -> dict:
        """

        Transform a SFilter to a where condition

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """

        if sf._operator == Operator.AND:
            sub_list = []
            for sub in sf._value:
                sub_list.append(self._sfilter_to_db_filter(sub))

            return f'( {" AND ".join( sub_list ) } )'

        if sf._operator == Operator.OR:
            sub_list = []
            for sub in sf._value:
                sub_list.append(self._sfilter_to_db_filter(sub))

            return f'( {" OR ".join( sub_list ) } )'

        if sf._operator == Operator.NOT:
            return f"( NOT ( {self._sfilter_to_db_filter(sf._value)} ) )"

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

        transformer: Transformer = self.get_transformer(db_path)
        if transformer:
            db_path = transformer.get_key_path()

        table_field_name = f"{self._main_table_name}.{'_'.join(db_path)}"

        if sf._operator == Operator.EQ:

            self.values.append(str(sf._value))
            return f"( {table_field_name} == ?)"

        if sf._operator == Operator.GT:
            if sql_type not in ["INTEGER", "REAL"]:
                raise DBError("Cannot do a gt on {0}", sf._path)

            self.values.append(sf._value)
            return f"( {table_field_name} > ?)"

        if sf._operator == Operator.GTE:
            if sql_type not in ["INTEGER", "REAL"]:
                raise DBError("Cannot do a gte on {0}", sf._path)

            self.values.append(str(sf._value))
            return f"( {table_field_name} >= ?)"

        if sf._operator == Operator.LTE:
            if sql_type not in ["INTEGER", "REAL"]:
                raise DBError("Cannot do a lte on {0}", sf._path)

            self.values.append(str(sf._value))
            return f"( {table_field_name} <= ?)"

        if sf._operator == Operator.LT:
            if sql_type not in ["INTEGER", "REAL"]:
                raise DBError("Cannot do a lt on {0}", sf._path)

            self.values.append(str(sf._value))
            return f"( {table_field_name} < ?)"

        if sf._operator == Operator.NE:

            self.values.append(str(sf._value))
            return f"( {table_field_name} != ?)"

        # Not implemented
        raise DBError(
            "Operator {0} not implemented in sqlite3 (path={1})", sf._operator, sf._path
        )

    def build_db_filter(self, backo_filter: SFilter) -> tuple[str, tuple[str]]:
        """

        Transform a SFilter to a sqlite query

        :param sf: The SFilter
        :type sf: SFilter
        :return: the mongo query
        :rtype: dict
        """
        self.values = []
        where_conditions = self._sfilter_to_db_filter(backo_filter)
        return (where_conditions, tuple(self.values))
