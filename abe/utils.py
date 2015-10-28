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


def to_unicode(data):
    """
    Ensure that dates, Decimals and strings become unicode
    """
    if isinstance(data, datetime):
        data = datetime_to_string(data)
    else:
        data = str(data)

    if not _PY3 and isinstance(data, str):
        data = unicode(data)
    return data
