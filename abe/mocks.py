import json

from supermutes.dot import dotify


class AbeMock(object):

    def __init__(self, filename):
        """
        Initialise an ABE mock from data.

        filename is expected to be the path to an ABE file.

        """
        with open(filename, 'r') as f:
            data = json.load(f)

        # map JSON fields to attributes
        self.__dict__ = data

        # Make all example requests and reponses accessible via dot syntax
        # (e.g. mock["OK"].request.status)
        for k, v in self.examples.items():
            self.examples[k] = dotify(v)
