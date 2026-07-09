"""
test for api toolbkx
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest


from werkzeug.datastructures import ImmutableMultiDict
from backo import multidict_to_filter, multidict_to_sfilter, SFilter, Operator, dict_to_sfilter


class TestApiToolbox(unittest.TestCase):
    """
    API toolbox tests
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

    def test_sub(self):
        """
        test sub
        """
        md = ImmutableMultiDict(
            [("a", "1"), ("toto", "1"), ("toto", "2"), ("b.c", "in"), ("b.d", "out")]
        )
        my_filter = multidict_to_filter(md)
        self.assertEqual(my_filter["a"], 1)
        self.assertNotEqual(my_filter["a"], "1")
        self.assertNotEqual(my_filter["toto"], ["1", "2"])
        self.assertEqual(my_filter["toto"], [1, 2])
        self.assertEqual(my_filter["b"]["c"], "in")
        self.assertEqual(my_filter["b"]["d"], "out")


    def test_multidict_to_sfilter(self):
        """
        test multidict_to_sfilter
        """
        md = ImmutableMultiDict(
            [("a", "1"), ("toto", "1"), ("toto", "2"), ("b.c.$gt", "12"), ("b.d", "3.14")]
        )
        my_filter:SFilter = multidict_to_sfilter(md)
        self.assertEqual(isinstance( my_filter, SFilter), True )
        # print(f'm={my_filter}')
        self.assertEqual(repr(my_filter), 'SFilter("None" Operator.AND \
[SFilter("$.a" Operator.EQ 1), SFilter("None" Operator.AND \
[SFilter("$.toto" Operator.EQ 1), SFilter("$.toto" Operator.EQ 2)])\
, SFilter("$.b.c" Operator.GT 12), SFilter("$.b.d" Operator.EQ 3.14)])')

    def test_dict_to_sfilter(self):
        """
        test dict_to_sfilter
        """
        f=dict_to_sfilter( { "$.a" : 12 } ) 
        self.assertEqual( str(f), 'SFilter("$.a" Operator.EQ 12)')
    
        f=dict_to_sfilter({ "$.a.$gt" : 12 })
        self.assertEqual( str(f), 'SFilter("$.a" Operator.GT 12)')
 
        f=dict_to_sfilter({ "$.a" : 12 , "$.b" : 22 })
        self.assertEqual( str(f), 'SFilter("None" Operator.AND [SFilter("$.a" Operator.EQ 12), SFilter("$.b" Operator.EQ 22)])')

        f=dict_to_sfilter({ "$not" : { "$.a" : 12 } })
        self.assertEqual( str(f), 'SFilter("None" Operator.NOT SFilter("$.a" Operator.EQ 12))')
        f=dict_to_sfilter({ "$or" : [{ "$.a" : 12 }, { "$.b" : 22 } ] })
        self.assertEqual( str(f), 'SFilter("None" Operator.OR [SFilter("$.a" Operator.EQ 12), SFilter("$.b" Operator.EQ 22)])')


    def test_sub_error(self):
        """
        test sub
        """
        md = ImmutableMultiDict([("a", "1"), ("b.c", "in"), ("b", "23")])
        my_filter = multidict_to_filter(md)
        self.assertEqual(my_filter["a"], 1)
        self.assertEqual(my_filter["b"], 23)

    def test_operators(self):
        """
        test_operators
        """
        md = ImmutableMultiDict([("a", "1"), ("toto.$gt", "1"), ("b.c.$re", "in")])
        my_filter = multidict_to_filter(md)
        self.assertEqual(my_filter["a"], 1)
        self.assertEqual(my_filter["toto"], ("$gt", 1))
        self.assertEqual(my_filter["b"]["c"], ("$re", "in"))
