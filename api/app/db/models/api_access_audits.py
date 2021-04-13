""" Class model that reflect resources and map to database tables relating audits created
by authenticated user requests.
"""
from sqlalchemy import (Column, Integer, String, Boolean, UniqueConstraint)
from app.db.database import Base
from app.db.models.common import TZTimeStamp


class APIAccessAudit(Base):
    """ Class representing table structure of 'audits' table in DB.
        Each record is immutably created for each authenticated API request
        based on IDIR username, request path and timestamp.
    """
    __tablename__ = 'api_access_audits'
    __table_args__ = (
        {'comment': 'The audit log of an authenticated request by a user.'}
    )
    id = Column(Integer, primary_key=True)
    create_user = Column(String, nullable=True, index=True)
    path = Column(String, nullable=False, index=True)
    create_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    success = Column(Boolean, nullable=False, default=False)
