""" CRUD for CHaines
"""
from datetime import timedelta
from sqlalchemy.orm import Session
from app.db.models import CHainesPoly
from app.time_utils import get_utc_now


def get_model_runs(session: Session):
    """ Get some recent model runs """
    return session.query(CHainesPoly.model_run_timestamp)\
        .filter(CHainesPoly.model_run_timestamp > get_utc_now() - timedelta(days=3))\
        .group_by(CHainesPoly.model_run_timestamp)\
        .order_by(CHainesPoly.model_run_timestamp)
