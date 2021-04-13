""" CRUD create function for audit logs
"""
from datetime import timezone, datetime
import logging
from sqlalchemy.exc import IntegrityError
from app.db.models import APIAccessAudit

import app.db.database

logger = logging.getLogger(__name__)


def create_api_access_audit_log(
        username: str,
        success: bool,
        path: str) -> APIAccessAudit:
    """ Create an audit log. """
    with app.db.database.get_write_session_scope() as session:
        now = datetime.now(tz=timezone.utc)
        audit_log = APIAccessAudit(create_user=username, path=path, success=success,
                                   create_timestamp=now)
        try:
            session.add(audit_log)
            session.commit()
        except IntegrityError:
            logger.info('Skipping duplicate record for username=%s @ %s for path=%s',
                        username, now, path)
            session.rollback()
