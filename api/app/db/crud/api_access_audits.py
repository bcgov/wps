""" CRUD create function for audit logs
"""
from app.time_utils import get_utc_now
import logging
from app.db.models import APIAccessAudit

import app.db.database

logger = logging.getLogger(__name__)


def create_api_access_audit_log(
        username: str,
        success: bool,
        path: str) -> None:
    """ Create an audit log. """
    with app.db.database.get_write_session_scope() as session:
        now = get_utc_now()
        audit_log = APIAccessAudit(create_user=username, path=path, success=success,
                                   create_timestamp=now)
        session.add(audit_log)
        session.commit()
