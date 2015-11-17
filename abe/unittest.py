import os

from .mocks import AbeMock
from .utils import normalize, subkeys


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

    def assert_item_matches(self, real, sample):
        """
        A primitive value matches the sample.

        If the sample represents a parameter, then do simple pattern matching.

        """
        real = normalize(real)
        sample = normalize(sample)
        self.assertEqual(real, sample)

    def assert_data_equal(self, real, sample, ignore=None):
        """
        Two elements are recursively equal

        :param ignore:
            Names of fields to ignore
        """
        ignore = ignore or []
        try:
            if isinstance(real, list):
                self.assertIsInstance(sample, list)
                self.assert_data_list_equal(real, sample, ignore)
            elif isinstance(real, dict):
                self.assertIsInstance(sample, dict)
                self.assert_data_dict_equal(real, sample, ignore)
            else:
                self.assert_item_matches(real, sample)
        except AssertionError as exc:
            message = str(exc) + '\n{}\n{}\n\n'.format(real, sample)
            raise type(exc)(message)

    def assert_data_dict_equal(self, real, sample, ignore=None):
        """
        Two dicts are recursively equal without taking order into account
        """
        ignore = ignore or []
        self.assertEqual(
            len(real), len(sample),
            msg='Number of elements mismatch: {} != {}\n'.format(
                real.keys(), sample.keys())
        )
        for key in real:
            if key not in ignore:
                self.assertIn(key, sample)
                inner_ignore = subkeys(ignore, key)
                self.assert_data_equal(real[key], sample[key], inner_ignore)

    def assert_data_list_equal(self, real, sample, ignore=None):
        """
        Two lists are recursively equal, including ordering.
        """
        ignore = ignore or []
        self.assertEqual(
            len(real), len(sample),
            msg='Number of elements mismatch: {} {}'.format(
                real, sample)
        )

        exceptions = []
        for real_item, sample_item in zip(real, sample):
            try:
                self.assert_data_equal(real_item, sample_item, ignore)
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

    def assert_matches_response(self, sample_response, wsgi_response,
                                ignore=None):
        """
        Check that the sample response and wsgi response match.
        """
        ignore = ignore or []
        self.assertEqual(wsgi_response.status_code, sample_response.status)
        if 'body' in sample_response:
            response_parsed = wsgi_response.data
            self.assert_data_equal(
                response_parsed, sample_response.body, ignore)

    def assert_matches_sample(self, path, label, response, ignore=None):
        """
        Check a URL and response against a sample.

        :param sample_name:
            The name of the sample file, e.g. 'query.json'
        :param label:
            The label for a specific sample request/response, e.g. 'OK'
        :param response:
            The actual API response we want to match with the sample.
            It is assumed to be a Django Rest Framework response object
        :param ignore:
            List of fields that will not be checked for strict matching.
            You can use this to include server-generated fields whose exact
            value you don't care about in your test, like ids, dates, etc.
        """
        ignore = ignore or []
        sample = self.load_sample(path)
        sample_request = sample.examples[label].request
        sample_response = sample.examples[label].response

        self.assert_matches_response(sample_response, response, ignore=ignore)
        self.assert_matches_request(sample_request, response.wsgi_request)
