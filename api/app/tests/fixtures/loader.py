""" Loading of fixtures """
import os
from collections import defaultdict
import json
import logging
from urllib.parse import urlencode, urlsplit
from pathlib import Path
from app import config, configure_logging


logger = logging.getLogger(__name__)


configure_logging()


class FixtureException(Exception):
    """ Exception for fixture related issues """


def nested_set(dic: dict, keys: list, value: object):
    """
    credit: https://stackoverflow.com/a/13688108/295741
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


class FixtureFinder():
    """ Use a lookup file to find the associated fixtured.
    The lookupfile is a dictionary that uses the verb, url, params and data as keys to find
    the appropriate fixture file:
    {
        'verb: e.g. one of get/post/put/delete':
        {
            'url: e.g. http://some.url.com/some/path':
            {
                'params: e.g. {'a': 1, 'b': 2}: {
                    'data: e.g. post data': filename
                }
            }
        }
    }
    """

    def __init__(self):
        super().__init__()

    def get_base_path(self, url: str):
        # break url into parts.
        split = urlsplit(url)
        # construct the base path.
        base_path = os.path.join(os.path.dirname(__file__), split.netloc)
        # check if it exists.
        if not os.path.exists(base_path):
            if config.get('AUTO_MAKE_FIXTURES'):
                # Make the fixture path if it doesn't exist - very useful for development.
                logger.warning('creating fixture base path {}'.format(base_path))
                Path(base_path).mkdir()
            raise FixtureException('unhandeled url: {}, fixture path ({}) does not exist'.format(
                url, base_path))
        return base_path

    def get_lookup_filename(self, base_path: str):
        return os.path.join(base_path, 'lookup.json')

    def load_lookup(self, base_path: str):
        self.lookup_file_name = self.get_lookup_filename(base_path)

        if not os.path.exists(self.lookup_file_name):
            if config.get('AUTO_MAKE_FIXTURES'):
                logger.warning('creating fixture lookup file {}'.format(
                    self.lookup_file_name))
                with open(self.lookup_file_name, 'w') as lookup_file:
                    return json.dump({}, lookup_file)
            raise FixtureException(
                'lookup file ({}) does not exist'.format(self.lookup_file_name))

        with open(self.lookup_file_name) as lookup_file:
            return json.load(lookup_file)

    def guess_filename(self, url: str, params: dict):
        parts = urlsplit(url)
        filename = parts.path.strip('/')
        if params:
            filename = filename + '_'
            for key, value in params.items():
                if type(value) == str:
                    value = value.replace(' ', '_')
                filename = '{}_{}_{}'.format(filename, key, value)
        filename = filename[:200] + '.json'
        logger.warn('I think a good filename for {} would be {}'.format(url, filename))
        return filename

    def lookup_fixture(self, lookup: dict, url: str, verb: str, params: dict = None, data: str = None) -> str:
        fixture = lookup.get(url, {}).get(verb, {}).get(str(params), {}).get(str(data), None)
        if fixture is None:
            if config.get('AUTO_MAKE_FIXTURES'):
                logger.warning('inserting fixture into lookup')
                nested_set(lookup, [url, verb, str(params), str(data)], self.guess_filename(url, params))
                with open(self.lookup_file_name, 'w') as lookup_file:
                    json.dump(lookup, lookup_file, indent=3)
            raise FixtureException(
                'could not find {} {} {} in lookup'.format(url, params, data))
        return fixture

    def get_fixture_path(self, url: str, verb: str, params: dict = None, data: str = None) -> str:
        """ Returns the path to a fixture based on url and params.
        """
        logger.info('finding a fixture for {}'.format(url))
        # get the base path of the fixture:
        base_path = self.get_base_path(url)
        # load the lookup dictionary:
        lookup = self.load_lookup(base_path)
        # get the fixture file
        fixture_filename = self.lookup_fixture(lookup, url, verb, params, data)
        # the filename has to be relative to the base path
        fixture_filename = os.path.join(base_path, fixture_filename)
        if not os.path.exists(fixture_filename):
            FixtureException('fixture file {} for {} not found.'.format(fixture_filename, url))
        logger.info('returning {} for {}'.format(fixture_filename, url))
        return fixture_filename


if __name__ == '__main__':
    url = 'http://www.something.com/what/a/thing'
    verb = 'get'
    params = {'a': 1, 'b': 2}
    data = None

    finder = FixtureFinder()
    print(finder.get_fixture_path(url, verb, params, data))
