from copy import copy
from operator import attrgetter
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
        sample_file = os.path.join(self.samples_root, sample_path)
        return AbeMock(sample_file)

    def get_sample_request(self, path, label):
        """
        Get the request body to send for a specific sample label.

        """
        sample = self.load_sample(path)
        sample_request = sample.examples[label].request
        return sample_request.body

    def assert_data_equal(self, data1, data2):
        """
        Two elements are recursively equal without taking order into account
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
        Two lists are recursively equal without taking order into account
        """
        self.assertEqual(
            len(data1), len(data2),
            msg='Number of elements mismatch: {} {}'.format(
                data1, data2)
        )

        data1_elements = copy(data1)
        for element2 in data2:
            fails, exceptions, found = [], [], False
            while data1_elements and not found:
                element = data1_elements.pop()
                try:
                    self.assert_data_equal(element, element2)
                    found = True
                except AssertionError as exc:
                    exceptions.append(exc)
                    fails.append(element)
                    if not data1_elements:
                        message = '\n*\n'.join(
                            map(attrgetter('message'), exceptions)
                        )
                        raise type(exceptions[0])(message)
            data1_elements.extend(fails)

    def assert_matches_sample(self, path, label, url, response):
        """
        Check a URL and response against a sample.

        :param sample_name:
            The name of the sample file, e.g. 'query.json'
        :param label:
            The label for a specific sample request/response, e.g. 'OK'
        :param url:
            The actual URL we want to compare with the sample
        :param response:
            The actual API response we want to match with the sample
        """
        sample = self.load_sample(path)
        sample_request = sample.examples[label].request
        sample_response = sample.examples[label].response

        self.assertEqual(url, sample_request.url)
        self.assertEqual(response.status_code, sample_response.status)
        self.assert_data_equal(response.data, sample_response.body)
