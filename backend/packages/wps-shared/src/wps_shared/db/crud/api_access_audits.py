""" CRUD create function for audit logs
"""
import logging
import wps_shared.db.database
from wps_shared.db.models.api_access_audits import APIAccessAudit
from wps_shared.utils.time import get_utc_now


logger = logging.getLogger(__name__)


def create_api_access_audit_log(
        username: str,
        success: bool,
        path: str) -> None:
    """ Create an audit log. """
    try:
        with wps_shared.db.database.get_write_session_scope() as session:
            now = get_utc_now()
            audit_log = APIAccessAudit(create_user=username, path=path, success=success,
                                       create_timestamp=now)
            session.add(audit_log)
            session.commit()
    except Exception as exception:
        logger.error(exception, exc_info=True)
        raise
