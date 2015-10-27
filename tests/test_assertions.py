from unittest import TestCase

from abe.unittest import AbeTestMixin


class TestDataListEqual(TestCase, AbeTestMixin):


    def test_simple_list_equality(self):
        self.assert_data_list_equal([1, 2], [1, 2])

    def test_simple_list_equality_for_ordering(self):
        self.assertRaises(
            AssertionError,
            self.assert_data_list_equal, [3, 1, 2], [2, 3, 1]
        )

    def test_list_equality_nested_items(self):
        self.assert_data_list_equal([[3, 1], 1, 2], [[3, 1], 1, 2])
        self.assert_data_list_equal(
            [[3, 1], {'foo': 'bar'}, 2],
            [[3, 1], {'foo': 'bar'}, 2]
        )
        self.assert_data_list_equal(
            [[3, 1], {'foo': [1, 2, 3]}, 2],
            [[3, 1], {'foo': [1, 2, 3]}, 2]
        )

    def test_list_equality_ordering_nested_items(self):
        nested_examples = [
            ([[3, 1], 1, 2], [[1, 3], 1, 2]),
            ([[3, 1], {'foo': 'bar'}, 2], [[3, 1], {'foo': 'dee'}, 2]),
            ([[3, 1], {'foo': [1, 2, 3]}, 2], [[3, 1], {'foo': [1, 3, 2]}, 2])
        ]
        for data1, data2 in nested_examples:
            self.assertRaises(
                AssertionError,
                self.assert_data_list_equal, data1, data2
            )
