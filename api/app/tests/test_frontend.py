""" Unit tests for front end """
import unittest

from unittest.mock import patch
from app.frontend import get_static_foldername


class TestFrontend(unittest.TestCase):
    """ Front end unit tests"""

    @patch('app.frontend.config.get')
    def test_get_static_foldername_not_exist(self, get_patch):
        """ If the configured folder doesn't exist, return the default static folder. """
        get_patch.return_value = 'folder_does_not_exist'
        self.assertTrue(get_static_foldername().endswith('static'))

    @patch('app.frontend.config.get')
    def test_get_static_foldername_exist(self, get_patch):
        """ If the configured folder does exist, we get it back """
        get_patch.return_value = '.'
        self.assertEqual(get_static_foldername(), '.')
