""" CRUD create function for audit logs
"""
import logging
from app.utils.time import get_utc_now
from db.models import APIAccessAudit

import db.database

logger = logging.getLogger(__name__)


def create_api_access_audit_log(
        username: str,
        success: bool,
        path: str) -> None:
    """ Create an audit log. """
    try:
        with db.database.get_write_session_scope() as session:
            now = get_utc_now()
            audit_log = APIAccessAudit(create_user=username, path=path, success=success,
                                       create_timestamp=now)
            session.add(audit_log)
            session.commit()
    except Exception as exception:
        logger.error(exception, exc_info=True)
        raise
