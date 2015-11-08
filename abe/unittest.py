import os

from .mocks import AbeMock
from .utils import to_unicode


class AbeTestMixin(object):
    """
    Mixin for unittest.TestCase to check against API samples.

    Example usage:

        class TestCase(AbeTestMixin, unittest.TestCase)
            ...

    """
    # Root directory to load samples from.
    samples_root = '.'

    def load_sample(self, sample_path):
        """
        Load a sample file into an AbeMock object.
        """
        sample_filename = os.path.join(self.samples_root, sample_path)
        return AbeMock.from_filename(sample_filename)

    def get_sample_request(self, path, label):
        """
        Get the request body to send for a specific sample label.

        """
        sample = self.load_sample(path)
        sample_request = sample.examples[label].request
        return sample_request.body

    def assert_data_equal(self, data1, data2):
        """
        Two elements are recursively equal
        """
        try:
            if isinstance(data1, list):
                self.assertIsInstance(data2, list)
                self.assert_data_list_equal(data1, data2)
            elif isinstance(data1, dict):
                self.assertIsInstance(data2, dict)
                self.assert_data_dict_equal(data1, data2)
            else:
                data1 = to_unicode(data1)
                data2 = to_unicode(data2)
                self.assertIsInstance(data2, data1.__class__)
                self.assertEqual(data1, data2)
        except AssertionError as exc:
            message = str(exc) + '\n{}\n{}\n\n'.format(data1, data2)
            raise type(exc)(message)

    def assert_data_dict_equal(self, data1, data2):
        """
        Two dicts are recursively equal without taking order into account
        """
        self.assertEqual(
            len(data1), len(data2),
            msg='Number of elements mismatch: {} != {}\n'.format(
                data1.keys(), data2.keys())
        )
        for key in data1:
            self.assertIn(key, data2)
            self.assert_data_equal(data1[key], data2[key])

    def assert_data_list_equal(self, data1, data2):
        """
        Two lists are recursively equal, including ordering.
        """
        self.assertEqual(
            len(data1), len(data2),
            msg='Number of elements mismatch: {} {}'.format(
                data1, data2)
        )

        exceptions = []
        for element, element2 in zip(data1, data2):
            try:
                self.assert_data_equal(element, element2)
            except AssertionError as exc:
                exceptions.append(exc)

        if exceptions:
            message = '\n*\n'.join(
                map(str, exceptions)
            )
            raise type(exceptions[0])(message)

    def assert_headers_contain(self, response_data, spec_data):
        """
        response_data headers contain all headers defined in spec_data
        """
        for expected_header, expected_value in spec_data.items():
            django_expected_header = (
                'HTTP_' + expected_header.upper().replace('-', '_')
            )
            actual_val = response_data.get(
                expected_header,
                response_data.get(django_expected_header)
            )
            self.assertEqual(
                expected_value, actual_val,
                "Incorrect or missing value specified for "
                "header {0}".format(expected_header)
            )

    def assert_matches_request(self, sample_request, wsgi_request):
        """
        Check that the sample request and wsgi request match.
        """
        self.assertEqual(wsgi_request.META['PATH_INFO'], sample_request['url'])
        self.assertEqual(wsgi_request.META['REQUEST_METHOD'],
                         sample_request['method'])

        if 'headers' in sample_request:
            self.assert_headers_contain(
                wsgi_request.META, sample_request['headers']
            )

        if 'body' in sample_request:
            self.assert_data_equal(wsgi_request.POST, sample_request['body'])

    def assert_matches_response(self, sample_response, wsgi_response):
        """
        Check that the sample response and wsgi response match.
        """
        self.assertEqual(wsgi_response.status_code, sample_response.status)
        if 'body' in sample_response:
            response_parsed = wsgi_response.data
            self.assert_data_equal(response_parsed, sample_response.body)

    def assert_matches_sample(self, path, label, response):
        """
        Check a URL and response against a sample.

        :param sample_name:
            The name of the sample file, e.g. 'query.json'
        :param label:
            The label for a specific sample request/response, e.g. 'OK'
        :param response:
            The actual API response we want to match with the sample.
            It is assumed to be a Django Rest Framework response object
        """
        sample = self.load_sample(path)
        sample_request = sample.examples[label].request
        sample_response = sample.examples[label].response

        self.assert_matches_response(sample_response, response)
        self.assert_matches_request(sample_request, response.wsgi_request)
