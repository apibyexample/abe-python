from os.path import abspath, dirname, join
from unittest import TestCase
import warnings

from mock import Mock

from abe.mocks import AbeMock
from abe.unittest import AbeTestMixin

DATA_DIR = join(dirname(abspath(__file__)), 'data')


class TestAssertDataEqual(TestCase, AbeTestMixin):

    def test_int_value_matches(self):
        self.assert_data_equal(3, 3)

    def test_int_value_mismatch(self):
        self.assertRaises(
            AssertionError,
            self.assert_data_equal, 3, 33
        )

    def test_int_vs_string_value_mismatch(self):
        self.assertRaises(
            AssertionError,
            self.assert_data_equal, 3, "3"
        )

    def test_string_value_matches(self):
        self.assert_data_equal("hello", "hello")

    def test_string_value_mismatch(self):
        self.assertRaises(
            AssertionError,
            self.assert_data_equal, "hell", "hello"
        )


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


class TestAssertHeadersEqual(TestCase, AbeTestMixin):

    def test_matches_django_test_format(self):
        self.assert_headers_contain(
            {'HTTP_THIS_CUSTOM_HEADER': 'Foo'},
            {'This-Custom-Header': 'Foo'}
        )

    def test_matches_normal_header_format(self):
        self.assert_headers_contain(
            {'This-Custom-Header': 'Foo'},
            {'This-Custom-Header': 'Foo'},
        )

    def test_matches_only_sample_defined_headers(self):
        self.assert_headers_contain(
            {'HTTP_THIS_CUSTOM_HEADER': 'Foo',
             'HTTP_SOME_UNDEFINED_IN_SPEC_HEADER': 'Bar'},
            {'This-Custom-Header': 'Foo'},
        )

    def test_requires_key_and_value_match(self):
        with self.assertRaises(AssertionError):
            self.assert_headers_contain(
                {'HTTP_THIS_CUSTOM_HEADER': 'Bar'},
                {'This-Custom-Header': 'Foo'},
            )
        with self.assertRaises(AssertionError):
            self.assert_headers_contain(
                {'HTTP_THIS_CUSTOM': 'Foo'},
                {'This-Custom-Header': 'Foo'},
            )


class TestAssertMatchesRequest(TestCase, AbeTestMixin):

    def setUp(self):
        abe_mock = AbeMock({
            "method": "POST",
            "url": "/resource/",
            "examples": {
                "OK": {
                    "request": {
                        "queryParams": {},
                        "body": {
                            "name": "My Resource"
                        },
                        "headers": {
                            "This-Custom-Header": 'Foo'
                        }
                    }
                }
            }
        })
        self.sample_request = abe_mock.examples['OK'].request

        self.mock_wsgi_request = Mock(
            POST={'name': 'My Resource'},
            META={
                'HTTP_THIS_CUSTOM_HEADER': 'Foo',
                'REQUEST_METHOD': 'POST',
                'PATH_INFO': '/resource/'
            },
        )

    def test_success_case(self):
        self.assert_matches_request(
            self.sample_request, self.mock_wsgi_request
        )

    def test_assertion_error_if_url_mismatch(self):
        self.mock_wsgi_request.META['PATH_INFO'] = '/resourceoops/'

        with self.assertRaises(AssertionError):
            self.assert_matches_request(
                self.sample_request, self.mock_wsgi_request
            )

    def test_assertion_error_if_method_mismatch(self):
        self.mock_wsgi_request.META['REQUEST_METHOD'] = 'PATCH'

        with self.assertRaises(AssertionError):
            self.assert_matches_request(
                self.sample_request, self.mock_wsgi_request
            )

    def test_assertion_error_if_post_data_mismatch(self):
        self.mock_wsgi_request.POST = {'a': 1}

        with self.assertRaises(AssertionError):
            self.assert_matches_request(
                self.sample_request, self.mock_wsgi_request
            )


class TestAssertMatchesResponse(TestCase, AbeTestMixin):

    def setUp(self):
        abe_mock = AbeMock({
            "method": "POST",
            "url": "/resource/",
            "examples": {
                "OK": {
                    "response": {
                        "status": 201,
                        "body": {
                            "id": 12,
                            "name": "My Resource",
                            "url": "http://example.com/resource/12",
                            "author": {
                                "name": "Slough",
                                "url": "http://example.com/user/25"
                            }
                        }
                    }
                }
            }
        })
        self.sample_response = abe_mock.examples['OK'].response

    def test_response_matches_strictly(self):
        response = Mock()
        response.status_code = 201
        response.data = {
            "id": 12,
            "name": "My Resource",
            "url": "http://example.com/resource/12",
            "author": {
                "name": "Slough",
                "url": "http://example.com/user/25"
            }
        }

        self.assert_matches_response(
            self.sample_response, response
        )

    def test_non_strict_response_matches(self):
        response = Mock()
        response.status_code = 201
        response.data = {
            "id": 25,
            "name": "My Resource",
            "url": "http://example.com/resource/12312",
            "author": {
                "name": "Slough",
                "url": "http://testserver/25/"
            }
        }

        self.assert_matches_response(
            self.sample_response, response, ignore=['id', 'url', 'author.url']
        )

    def test_non_strict_list_value_matches(self):
        abe_mock = AbeMock({
            "url": "/resource/",
            "method": "GET",
            "examples": {
                "OK": {
                    "response": {
                        "status": 200,
                        "body": {
                            "contributors": [
                                {"name": "Jack", "id": 1},
                                {"name": "Jill", "id": 2},
                            ]
                        }
                    }
                }
            }
        })
        sample = abe_mock.examples['OK'].response
        response = Mock()
        response.status_code = 200
        response.data = {
            "contributors": [
                {"name": "Jack", "id": 12},
                {"name": "Jill", "id": 23},
            ]
        }

        self.assert_matches_response(
            sample, response, ignore=['contributors.id']
        )


class TestFilenameInstantiation(TestCase):

    def setUp(self):
        self.filename = join(DATA_DIR, 'sample.json')

    def test_can_still_use_deprecated_instantiation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            AbeMock(self.filename)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_from_filename(self):
        AbeMock.from_filename(self.filename)
