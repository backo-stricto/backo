"""
The toolbox for api
A set of functions
"""

import re
import json
from typing import Any
from flask import Request
from werkzeug.datastructures import ImmutableMultiDict
from stricto import SFilter, Operator, SSyntaxError


def _get_operator(s: str) -> Operator:
    """
    find the operator from a string

    :example: "$gt" -> Operator.GT

    :param s: the string
    :type s: str
    :return: the operator found
    :rtype: Operator
    """
    a = {
        "$eq": Operator.EQ,
        "$ne": Operator.NE,
        "$gt": Operator.GT,
        "$gte": Operator.GTE,
        "$lt": Operator.LT,
        "$lte": Operator.LTE,
        "$reg": Operator.REG,
        "$all": Operator.ALL,
        "$contains": Operator.CONTAINS,
        "$size": Operator.SIZE,
        "$and": Operator.AND,
        "$or": Operator.OR,
        "$not": Operator.NOT,
    }

    return a.get(s)


def append_path_to_dict(the_dict: dict, key: str, value: list | tuple):
    """transform a

    :param the_dict: the dict to modify
    :type the_dict: dict
    :param key: the path
    :type key: str
    :param value: the value to insert
    :type value: list | tuple
    """
    changed_value = value
    if isinstance(value, list):
        # Transform string to int or float if we can
        typed_value = []
        for v in value:
            try:
                vv = int(v)
            except ValueError:
                try:
                    vv = float(v)
                except ValueError:
                    vv = v
            typed_value.append(vv)

        if len(typed_value) == 1:
            changed_value = typed_value[0]
        elif (
            len(typed_value) == 2
            and isinstance(typed_value[0], str)
            and re.findall(r"^\$", typed_value[0])
        ):
            changed_value = (typed_value[0], typed_value[1])
        else:
            changed_value = typed_value

    match = re.search(r"^([^\.]+)\.(.*)", key)
    if not match:
        the_dict[key] = changed_value
        return

    sub = the_dict.get(match.group(1), {})
    if not isinstance(sub, dict):
        sub = {}

    append_path_to_dict(sub, match.group(2), value)
    the_dict[match.group(1)] = sub


def _str_to_typed_value(s: str) -> int | float | str:
    """
    change a str to int or float

    :param s: the string to change
    :type s: str
    :return: the new typed value
    :rtype: int | float | str
    """

    v = s
    try:
        v = int(s)
    except ValueError:
        try:
            v = float(s)
        except ValueError:
            v = s
    return v


def multidict_to_sfilter(md: ImmutableMultiDict) -> SFilter:
    """
    Transform a multi dict to filter (query string are immutable dict)

    see match in stricto for definition of a filter
    see https://tedboy.github.io/flask/generated/generated/werkzeug.ImmutableMultiDict.html


    [ ('toto', 'miam'), ('titi.tutu', '23.2') ('tata.$gt', 11)] ->
    {
        'toto' : "miam",
        'titi' : {
            'tutu' : 23.2
        },
        'tata' : ( '$gt', 11 )
    }
    """

    list_of_filters = []
    for key in md.keys():

        # ignoring keys starting with _
        if re.match(r"^_", key):
            continue

        my_key = key
        value_as_list = md.getlist(key)

        operator = Operator.EQ
        match = re.search(r"(.*)\.(\$.*)$", key)
        if match:
            my_key = match[1]
            operator = _get_operator(match[2])

        if operator is None:
            raise SSyntaxError(f'Filter unknown operator "{match[2]}"')

        # if the key doesn’t start as a path, add "$." at the beginning
        if not re.match(r"^[\$\@]\.", my_key):
            my_key = f"$.{my_key}"

        # print(f'{my_key}={value_as_list}')

        if len(value_as_list) == 1:
            list_of_filters.append(
                SFilter(my_key, operator, _str_to_typed_value(value_as_list[0]))
            )
        else:
            l = []
            for v in value_as_list:
                l.append(SFilter(my_key, operator, _str_to_typed_value(v)))
            list_of_filters.append(SFilter(None, Operator.AND, l))

    if len(list_of_filters) == 0:
        return SFilter(None, Operator.TRUE, None)
    if len(list_of_filters) == 1:
        return list_of_filters[0]

    return SFilter(None, Operator.AND, list_of_filters)


def dict_to_sfilter(d: dict) -> SFilter:  # pylint: disable=too-many-branches
    """Transform a dict into a SFilter


    { "$.a" : 12 } -> SFilter( "$.a", Operator.EQ, 12)
    { "$.a.$gt" : 12 } -> SFilter( "$.a", Operator.GT, 12)

    { "$.a" : 12 , "$.b" : 22 } -> SFilter( None, Operator.AND, [ SFilter( "$.a", Operator.EQ, 12), SFilter( "$.b", Operator.EQ, 22) ])
    { "$not" : { "$.a" : 12 } } -> SFilter( None, Operator.NOT, SFilter( "$.a", Operator.EQ, 12))
    { "$or" : [{ "$.a" : 12 }, { "$.b" : 22 } ] } -> SFilter( None, Operator.OR, [ SFilter( "$.a", Operator.EQ, 12), SFilter( "$.b", Operator.EQ, 22) )

    Args:
        d (dict): _description_

    Returns:
        SFilter: _description_
    """

    if d is None:
        return SFilter(None, Operator.TRUE, None)

    list_of_sfilter = []
    for key, value in d.items():

        # $not operator
        if key == "$not":
            if not isinstance(value, dict):
                raise SSyntaxError('"$not" operator must be followed by a dict')
            return SFilter(None, Operator.NOT, dict_to_sfilter(value))

        # $and and $or
        if key in ("$or", " $and"):
            if not isinstance(value, list):
                raise SSyntaxError(
                    '"$or" and "$and" operator must be followed by a list of dict'
                )
            operator = _get_operator(key)
            l = []
            for v in value:
                if not isinstance(v, dict):
                    raise SSyntaxError(
                        '"$or" and "$and" operator must be followed by a list of dict'
                    )
                l.append(dict_to_sfilter(v))
            return SFilter(None, operator, l)

        # An operator at the end
        my_key = key

        operator = Operator.EQ
        match = re.search(r"(.*)\.(\$.*)$", key)
        if match:
            my_key = match[1]
            operator = _get_operator(match[2])

        if operator is None:
            raise SSyntaxError(f'Filter unknown operator "{match[2]}"')

        # if the key doesn’t start as a path, add "$." at the beginning
        if not re.match(r"^[\$\@]\.", my_key):
            my_key = f"$.{my_key}"

        list_of_sfilter.append(SFilter(my_key, operator, value))

    # return the filter
    if len(list_of_sfilter) == 0:
        return SFilter(None, Operator.TRUE, None)
    if len(list_of_sfilter) == 1:
        return list_of_sfilter[0]

    return SFilter(None, Operator.AND, list_of_sfilter)


def request_to_object(request: Request) -> Any:
    """Read the request and transform it to a struct

    :param request: The request given
    :type request: Request
    """

    # Json, return just the json
    if request.content_type == "application/json":
        return request.json

    if re.match(r"^multipart/form-data;", request.content_type):
        obj = {}
        if "_json" in request.form:
            obj = json.loads(request.form.get("_json"))

        # Adding other keys
        for key in request.form:
            value = request.form[key]
            # ignoring keys starting with _
            if re.match(r"^_", key):
                continue

            append_path_to_dict(obj, key, value)

        # Append files to the json struct
        for vpath in request.files:
            file = request.files[vpath]
            append_path_to_dict(obj, vpath, file)

        return obj

    return None
