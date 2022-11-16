""" Unit tests for api_access_audit_log """
import unittest
from unittest.mock import MagicMock, patch
from db.crud.api_access_audits import create_api_access_audit_log


class TestApiAccessAudit(unittest.TestCase):
    """ Access audit test cases """

    @patch('db.database._get_write_session', return_value=MagicMock())
    @patch('db.crud.api_access_audits.logger')
    def test_exception_logged(self, mock_logger, mock_get_write_session):
        # Create a mock object that raises an exception when commit is called.
        mock_session = MagicMock()
        mock_session.commit = MagicMock(side_effect=Exception())
        mock_get_write_session.return_value = mock_session

        # We expect an exception to be thrown when we do the audit log
        with self.assertRaises(Exception):
            create_api_access_audit_log('user', True, '/something')
        # But - critically, we expect the exception to be logged.
        mock_logger.error.assert_called()
