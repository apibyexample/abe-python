from unittest import TestCase

from abe.utils import subkeys


class TestSubkeys(TestCase):
    def test_subkeys(self):
        new_keys = subkeys(['key.one', 'key.two', 'hello', 'keyring'], 'key')
        self.assertEqual(new_keys, ['one', 'two'])
