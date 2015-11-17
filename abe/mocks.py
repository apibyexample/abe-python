import json
import warnings

from supermutes.dot import dotify


class AbeMock(object):

    def __init__(self, data):
        """
        Initialise an ABE mock from data.

        """
        if not isinstance(data, dict):
            msg = ('Instanciating an AbeMock by filename is deprecated and '
                   'will be removed in an upcoming release. '
                   'Use AbeMock.from_filename instead'.format(data))
            warnings.warn(msg, DeprecationWarning)
            with open(data, 'r') as f:
                data = json.load(f)

        # map JSON fields to attributes
        self.__dict__ = data

        # Make all example requests and reponses accessible via dot syntax
        # (e.g. mock["OK"].request.status)
        for key, value in self.examples.items():
            # Add the request URL automatically if missing.
            self._feed_inherited_fields(value, 'request', ['url', 'method'])
            self.examples[key] = dotify(value)

    @classmethod
    def from_filename(cls, filename):
        """
        Initialise an ABE mock from a spec file.

        filename is expected to be the path to an ABE file.

        """
        with open(filename, 'r') as f:
            data = json.load(f)
        return AbeMock(data)

    def _feed_inherited_fields(self, value, where, inheritable):
        """
        If missing in request or response, some fields are inherited.

        URL and method are defined at the top level. They don't need to be
        redefined in example requests or responses.

        :param where: 'request' or 'response'
        :param inheritable: list of inheritable fields

        """
        if where not in value:
            value[where] = {}
        for key in inheritable:
            if key not in value[where]:
                value[where][key] = getattr(self, key)
