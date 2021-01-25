""" CRUD for CHaines
"""
from datetime import timedelta, datetime
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from app.db.models import CHainesPrediction, CHainesModelRun, PredictionModel
from app.time_utils import get_utc_now


def get_c_haines_model_run(session: Session, model_run_timestamp: datetime, prediction_model: PredictionModel):
    return session.query(CHainesModelRun).filter(
        CHainesModelRun.model_run_timestamp == model_run_timestamp,
        CHainesModelRun.prediction_model_id == prediction_model.id
    ).first()


def create_c_haines_model_run(session: Session, model_run_timestamp: datetime, prediction_model: PredictionModel):
    model_run = CHainesModelRun(model_run_timestamp=model_run_timestamp,
                                prediction_model=prediction_model)
    session.add(model_run)
    return model_run


def get_or_create_c_haines_model_run(session: Session, model_run_timestamp: datetime, prediction_model: PredictionModel):
    model_run = get_c_haines_model_run(session, model_run_timestamp, prediction_model)
    if not model_run:
        model_run = create_c_haines_model_run(session, model_run_timestamp, prediction_model)
    return model_run


def get_c_haines_prediction(
        session: Session,
        model_run: CHainesModelRun,
        prediction_timestamp: datetime):
    """ Get the c-haines prediction """
    return session.query(CHainesPrediction)\
        .filter(CHainesPrediction.model_run_id == model_run.id,
                CHainesPrediction.prediction_timestamp == prediction_timestamp)


def get_model_run_predictions(session: Session, model_run_timestamp: datetime):
    """ Get some recent model runs """
    if model_run_timestamp:
        # Get the day before and after the specified timestamp.
        end_date = model_run_timestamp + timedelta(days=1)
        start_date = model_run_timestamp - timedelta(days=1)
    else:
        # No timestamp? Get the last three days.
        end_date = get_utc_now()
        start_date = get_utc_now() - timedelta(days=3)

    query = session.query(CHainesModelRun.id,
                          CHainesModelRun.model_run_timestamp,
                          PredictionModel.name, PredictionModel.abbreviation,
                          CHainesPrediction.prediction_timestamp)\
        .join(CHainesModelRun, CHainesModelRun.id == CHainesPrediction.model_run_id)\
        .join(PredictionModel, PredictionModel.id == CHainesModelRun.prediction_model_id)\
        .filter(CHainesModelRun.model_run_timestamp >= start_date,
                CHainesModelRun.model_run_timestamp < end_date)\
        .order_by(desc(CHainesModelRun.model_run_timestamp), CHainesModelRun.id,
                  asc(CHainesPrediction.prediction_timestamp))
    return query

    # return session.query(
    #     CHainesPrediction.model_run_timestamp,
    #     CHainesPrediction.prediction_timestamp,
    #     PredictionModel.id,
    #     PredictionModel.name,
    #     PredictionModel.abbreviation)
    # .join(PredictionModel, PredictionModel.id == CHainesPrediction.prediction_model_id)
    # .filter(CHainesPrediction.model_run_timestamp >= start_date)
    # .order_by(desc(CHainesPrediction.model_run_timestamp), asc(CHainesPrediction.prediction_timestamp))
