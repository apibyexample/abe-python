from datetime import datetime
import sys

_PY3 = sys.version_info >= (3, 0)

if _PY3:
    unicode = str


def datetime_to_string(value):
    representation = value.isoformat()
    if value.microsecond:
        representation = representation[:23] + representation[26:]
    if representation.endswith('+00:00'):
        representation = representation[:-6] + 'Z'
    return representation


def normalize(data):
    """
    Ensure that dates, Decimals and strings become unicode

    Integers, on the other hand, are not converted.
    """
    if isinstance(data, datetime):
        data = datetime_to_string(data)
    elif not isinstance(data, int):
        data = str(data)

    if not _PY3 and isinstance(data, str):
        data = unicode(data)
    return data


def subkeys(original, key):
    """
    Takes a list of dot-hierarchical values and keeps only matching subkeys.

    Example:

    >>> subkeys(['one.two', 'one.three', 'four'], 'one')
    ['two', 'three']
    """
    new_keys = filter(lambda s: s.startswith(key + '.'), original)
    new_keys = list(map(lambda s: s[len(key) + 1:], new_keys))
    return new_keys
