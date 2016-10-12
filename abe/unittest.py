import os
try:
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import parse_qs

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

    def assert_data_equal(self, real, sample, non_strict=None):
        """
        Two elements are recursively equal

        :param non_strict:
            Names of fields to match non-strictly. In current implementation,
            only check for field presence.
        """
        non_strict = non_strict or []
        try:
            if isinstance(real, list):
                self.assertIsInstance(sample, list)
                self.assert_data_list_equal(real, sample, non_strict)
            elif isinstance(real, dict):
                self.assertIsInstance(sample, dict)
                self.assert_data_dict_equal(real, sample, non_strict)
            else:
                self.assert_item_matches(real, sample)
        except AssertionError as exc:
            message = str(exc) + '\n{}\n{}\n\n'.format(real, sample)
            raise type(exc)(message)

    def assert_data_dict_equal(self, real, sample, non_strict=None):
        """
        Two dicts are recursively equal without taking order into account
        """
        non_strict = non_strict or []
        self.assertEqual(
            len(real), len(sample),
            msg='Number of elements mismatch: {} != {}\n'.format(
                real.keys(), sample.keys())
        )
        for key in sample:
            self.assertIn(key, real)
            if key not in non_strict:
                inner_non_strict = subkeys(non_strict, key)
                self.assert_data_equal(
                    real[key], sample[key], inner_non_strict)

    def assert_data_list_equal(self, real, sample, non_strict=None):
        """
        Two lists are recursively equal, including ordering.
        """
        non_strict = non_strict or []
        self.assertEqual(
            len(real), len(sample),
            msg='Number of elements mismatch: {} {}'.format(
                real, sample)
        )

        exceptions = []
        for real_item, sample_item in zip(real, sample):
            try:
                self.assert_data_equal(real_item, sample_item, non_strict)
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

    def assert_query_params_equal(self, request_data, spec_data):
        qs = parse_qs(request_data)
        for k, expected_value in spec_data.items():
            try:
                actual_value = qs[k]
            except KeyError:
                raise AssertionError('Missing {0} from request'.format(k))

            if len(actual_value) == 1:
                actual_value = actual_value[0]
            self.assertEqual(expected_value, actual_value)

    def assert_matches_request(self, sample_request, wsgi_request,
                               non_strict=None):
        """
        Check that the sample request and wsgi request match.
        """
        non_strict = non_strict or []

        if 'url' not in non_strict:
            self.assertEqual(wsgi_request.META['PATH_INFO'],
                             sample_request['url'])
        if 'method' not in non_strict:
            self.assertEqual(wsgi_request.META['REQUEST_METHOD'],
                             sample_request['method'])

        if 'headers' in sample_request and 'headers' not in non_strict:
            self.assert_headers_contain(
                wsgi_request.META, sample_request['headers']
            )

        if 'queryParams' in sample_request and 'queryParams' not in non_strict:
            self.assert_query_params_equal(
                wsgi_request.META['QUERY_STRING'],
                sample_request['queryParams']
            )

        if 'body' in sample_request:
            self.assert_data_equal(
                wsgi_request.POST, sample_request['body'], non_strict)

    def assert_matches_response(self, sample_response, wsgi_response,
                                non_strict=None):
        """
        Check that the sample response and wsgi response match.
        """
        non_strict = non_strict or []
        self.assertEqual(wsgi_response.status_code, sample_response.status)
        if 'body' in sample_response:
            response_parsed = wsgi_response.data
            self.assert_data_equal(
                response_parsed, sample_response.body, non_strict)

    def assert_matches_sample(
        self, path, label, response, non_strict_response=None,
        non_strict_request=None
    ):
        """
        Check a URL and response against a sample.

        :param sample_name:
            The name of the sample file, e.g. 'query.json'
        :param label:
            The label for a specific sample request/response, e.g. 'OK'
        :param response:
            The actual API response we want to match with the sample.
            It is assumed to be a Django Rest Framework response object
        :param non_strict:
            List of fields that will not be checked for strict matching.
            You can use this to include server-generated fields whose exact
            value you don't care about in your test, like ids, dates, etc.
        """
        non_strict_response = non_strict_response or []
        non_strict_request = non_strict_request or []
        sample = self.load_sample(path)
        sample_request = sample.examples[label].request
        sample_response = sample.examples[label].response

        self.assert_matches_response(
            sample_response, response, non_strict=non_strict_response)
        self.assert_matches_request(
            sample_request, response.wsgi_request,
            non_strict=non_strict_request)
