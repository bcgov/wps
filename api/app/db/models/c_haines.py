""" Class models that reflect resources and map to database tables Continuous Haines.
"""
import enum
from sqlalchemy import (Column, Integer,
                        Sequence, ForeignKey, UniqueConstraint, Enum)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.database import Base
from app.db.models.common import TZTimeStamp


class SeverityEnum(enum.Enum):
    """ Enumerated values for severity
    """
    LOW = "<4"
    MODERATE = "4-8"
    HIGH = "8-11"
    EXTREME = ">11"


severity_levels = [item.value for item in SeverityEnum]


class CHainesModelRun(Base):
    """ C-Haines model run """
    __tablename__ = 'c_haines_model_runs'
    __table_args__ = (
        UniqueConstraint('model_run_timestamp', 'prediction_model_id'),
        {'comment': 'Identifies the model run and prediction for a particular set of c-haines calculations'}
    )

    id = Column(Integer, Sequence('c_haines_model_runs_id_seq'),
                primary_key=True, nullable=False, index=True)
    model_run_timestamp = Column(TZTimeStamp, nullable=False)
    prediction_model_id = Column(Integer, ForeignKey(
        'prediction_models.id'), nullable=False)
    prediction_model = relationship("PredictionModel")

    def __str__(self):
        return (f'id:{self.id}, '
                f'model_run_timestamp:{self.model_run_timestamp}, '
                f'prediction_model_id:{self.prediction_model_id}')


class CHainesPrediction(Base):
    """ C-Haines model run predictions """
    __tablename__ = 'c_haines_predictions'
    __table_args__ = (
        UniqueConstraint('prediction_timestamp', 'model_run_id'),
        {'comment': 'Identifies the model run and prediction for a particular set of c-haines calculations'}
    )

    id = Column(Integer, Sequence('c_haines_predictions_id_seq'),
                primary_key=True, nullable=False, index=True)
    prediction_timestamp = Column(TZTimeStamp, nullable=False)
    model_run_id = Column(Integer, ForeignKey(
        'c_haines_model_runs.id'), nullable=False)
    model_run = relationship("CHainesModelRun")

    def __str__(self):
        return (f'id:{self.id}, '
                f'prediction_timestamp:{self.prediction_timestamp}, '
                f'model_run_id:{self.model_run_id}')


class CHainesPoly(Base):
    """ C-Haines polygons """
    __tablename__ = 'c_haines_polygons'

    id = Column(Integer, Sequence('c_haines_polygons_id_seq'),
                primary_key=True, nullable=False, index=True)
    geom = Column(Geometry('POLYGON'), nullable=False)
    # Depending on the severity of the C-Haines index, we group c-haines
    # ranges together. (Fire Behaviour analysts only care of the
    # C-Haines is high)
    c_haines_index = Column(Enum(*severity_levels, name="c_haines_severity_levels"), nullable=False)

    c_haines_prediction_id = Column(Integer, ForeignKey(
        'c_haines_predictions.id'), nullable=False)
    c_haines_prediction = relationship('CHainesPrediction')
