""" CRUD for CHaines
"""
from datetime import timedelta, datetime
from sqlalchemy.orm import Session
from app.db.models import CHainesPoly
from app.time_utils import get_utc_now


def get_model_runs(session: Session):
    """ Get some recent model runs """
    return session.query(CHainesPoly.model_run_timestamp, CHainesPoly.prediction_timestamp)\
        .filter(CHainesPoly.model_run_timestamp > get_utc_now() - timedelta(days=3))\
        .group_by(CHainesPoly.model_run_timestamp, CHainesPoly.prediction_timestamp)\
        .order_by(CHainesPoly.model_run_timestamp, CHainesPoly.prediction_timestamp)


# def get_model_run_predictions(session: Session, model_run_timestamp: datetime):
#     return session.query(CHainesPoly.prediction_timestamp)\
#         .filter(CHainesPoly.model_run_timestamp == model_run_timestamp)\
#         .group_by(CHainesPoly.prediction_timestamp)\
#         .order_by(CHainesPoly.prediction_timestamp)
