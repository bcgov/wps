""" Code for automatic loading of fixture files based on requests. """
import os
from collections import defaultdict
import json
import logging
from urllib.parse import urlencode, urlsplit
from pathlib import Path
from app import config


logger = logging.getLogger(__name__)


class FixtureException(Exception):
    """ Exception for fixture related issues """


def nested_defaultdict(existing=None, **kwargs):
    """ Created an infintely nested default dict from an existing dict.
    credit: https://stackoverflow.com/a/62438324/295741
    """
    if existing is None:
        existing = {}
    if not isinstance(existing, dict):
        return existing
    existing = {key: nested_defaultdict(val) for key, val in existing.items()}
    return defaultdict(nested_defaultdict, existing, **kwargs)


class FixtureFinder():
    """ Use a lookup file to find the associated fixtured.
    The lookupfile is a dictionary that uses the verb (e.g. get, post, put, etc), url, params and data as 
    keys to find the appropriate fixture file:
    {
        '<verb>': {
            '<url>': {
                '<params>': {
                    '<data>': <filename>
                }
            }
        }
    }
    e.g. a get query http://thing?a=1 that servers up some file.json would be:
    {
        "get": {"http://thing": {{"'a': 1": "None": "file.json"}}}
    }

    If the environment variable AUTO_MAKE_FIXTURES is set to True, it will attempt to create some files
    and folder structures for you. (This is useful when developing.)
    """

    def get_base_path(self, url: str):
        """ Get the bast path of the provided url.
        """
        # break url into parts.
        split = urlsplit(url)
        # construct the base path.
        base_path = os.path.join(os.path.dirname(__file__), split.netloc)
        # check if it exists.
        if not os.path.exists(base_path):
            if config.get('AUTO_MAKE_FIXTURES'):
                # Make the fixture path if it doesn't exist - very useful for development.
                logger.warning('creating fixture base path %s', base_path)
                Path(base_path).mkdir()
            raise FixtureException('unhandeled url: {}, fixture path ({}) does not exist'.format(
                url, base_path))
        return base_path

    def get_lookup_filename(self, base_path: str):
        """ Get the filename of the json containing the lookup dictionary. """
        return os.path.join(base_path, 'lookup.json')

    def load_lookup(self, base_path: str):
        """ Load the lookup dictionary. """
        self.lookup_file_name = self.get_lookup_filename(base_path)

        if not os.path.exists(self.lookup_file_name):
            if config.get('AUTO_MAKE_FIXTURES'):
                logger.warning('creating fixture lookup file %s', self.lookup_file_name)
                with open(self.lookup_file_name, 'w') as lookup_file:
                    return json.dump({}, lookup_file)
            raise FixtureException(
                'lookup file ({}) does not exist'.format(self.lookup_file_name))

        with open(self.lookup_file_name) as lookup_file:
            return json.load(lookup_file)

    def guess_filename(self, url: str, params: dict):
        """ Guess a filename for the fixture. Only used when AUTO_MAKE_FIXTURES is True. """
        parts = urlsplit(url)
        filename = parts.path.strip('/')
        if params:
            filename = filename + '_'
            for key, value in params.items():
                if type(value) == str:
                    value = value.replace(' ', '_')
                filename = '{}_{}_{}'.format(filename, key, value)
        filename = filename[:200] + '.json'
        logger.warning('I think a good filename for %s would be %s', url, filename)
        return filename

    def lookup_fixture_filename(self,
                                lookup: dict,
                                url: str,
                                verb: str,
                                params: dict = None,
                                data: str = None) -> str:
        """ Given the request, find the name of the fixture. """
        # turn our dictionary into a supercharged nested dictionary
        lookup = nested_defaultdict(lookup)
        fixture = lookup[url][verb][str(params)][str(data)]

        if type(fixture) is not str:
            if config.get('AUTO_MAKE_FIXTURES'):
                logger.warning('inserting fixture into lookup')
                lookup[url][verb][str(params)][str(data)] = self.guess_filename(url, params)
                with open(self.lookup_file_name, 'w') as lookup_file:
                    json.dump(lookup, lookup_file, indent=3)
            raise FixtureException(
                'could not find {} {} {} in lookup'.format(url, params, data))
        return fixture

    def get_fixture_path(self, url: str, verb: str, params: dict = None, data: str = None) -> str:
        """ Returns the path to a fixture based on url and params.
        """
        logger.debug('finding a fixture for %s', url)
        # get the base path of the fixture:
        base_path = self.get_base_path(url)
        # load the lookup dictionary:
        lookup = self.load_lookup(base_path)
        # get the fixture file
        fixture_filename = self.lookup_fixture_filename(lookup, url, verb, params, data)
        # the filename has to be relative to the base path
        fixture_filename = os.path.join(base_path, fixture_filename)
        if not os.path.exists(fixture_filename):
            raise FixtureException('fixture file {} for {} not found.'.format(fixture_filename, url))
        logger.debug('returning %s for %s', fixture_filename, url)
        return fixture_filename
