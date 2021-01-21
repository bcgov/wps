""" CRUD for CHaines
"""
from datetime import timedelta
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.db.models import CHainesPoly, CHainesPrediction, PredictionModel
from app.time_utils import get_utc_now


def get_model_runs(session: Session):
    """ Get some recent model runs """
    start_date = get_utc_now() - timedelta(days=3)
    return session.query(
        CHainesPrediction.model_run_timestamp,
        CHainesPrediction.prediction_timestamp,
        PredictionModel.name,
        PredictionModel.abbreviation)\
        .join(PredictionModel, PredictionModel.id == CHainesPrediction.prediction_model_id)\
        .filter(CHainesPrediction.model_run_timestamp >= start_date)\
        .order_by(desc(CHainesPrediction.model_run_timestamp), CHainesPrediction.prediction_timestamp)


# def get_model_run_predictions(session: Session, model_run_timestamp: datetime):
#     return session.query(CHainesPoly.prediction_timestamp)\
#         .filter(CHainesPoly.model_run_timestamp == model_run_timestamp)\
#         .group_by(CHainesPoly.prediction_timestamp)\
#         .order_by(CHainesPoly.prediction_timestamp)
