""" Class models that reflect resources and map to database tables
"""

from sqlalchemy import (Column, String, Integer, Float,
                        TIMESTAMP, Sequence, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from app.db.database import Base


class ProcessedModelRunFile(Base):
    """ Record to indicate that a particular model run file has been processed.
    NOTE: One could check if values for a particular model run exists, but that would make it more
    difficult to re-process files as you'd have to delete existing values.
    """
    __tablename__ = 'processed_model_run_files'
    __table_args__ = (
        {'comment': 'Record to indicate that a particular model run file has been processed.'})
    # Unique identifier.
    id = Column(Integer, Sequence('processed_model_run_files_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Source URL of file processed.
    url = Column(String, nullable=False, unique=True)
    # Date this record was created.
    create_date = Column(TIMESTAMP(timezone=True), nullable=False)
    # Date this record was updated.
    update_date = Column(TIMESTAMP(timezone=True), nullable=False)


class PredictionModel(Base):
    """ Identifies the Weather Prediction model (e.g. GDPS 15km resolution). """
    __tablename__ = 'prediction_models'
    __table_args__ = (
        UniqueConstraint('abbreviation', 'projection'),
        {'comment': 'Identifies the Weather Prediction model'}
    )

    id = Column(Integer, Sequence('prediction_models_id_seq'),
                primary_key=True, nullable=False, index=True)
    # E.g. Global Deterministic Prediction System
    name = Column(String, nullable=False)
    # E.g. GDPS
    abbreviation = Column(String, nullable=False)
    # E.g. latlon.15x15
    # NOTE: we may want to consider not bothering with projection, since we would store it as geopgraphical
    # regardles. A better approach may be to just store the resolution: "15x15"
    projection = Column(String, nullable=False)


class PredictionModelRun(Base):
    """ Identify which prediction model run (e.g.  2020 07 07 12:00)."""
    __tablename__ = 'prediction_model_runs'
    __table_args__ = (
        UniqueConstraint('prediction_model_id', 'prediction_run_timestamp'),
        {
            'comment':
            'Identify which prediction model run (e.g.  2020 07 07 12:00).'
        }
    )

    id = Column(Integer, Sequence('prediction_model_runs_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Is it GPDS or RDPS?
    prediction_model_id = Column(Integer, ForeignKey(
        'prediction_models.id'), nullable=False)
    prediction_model = relationship("PredictionModel")
    # The date and time of the model run.
    prediction_run_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)


class PredictionModelGridSubset(Base):
    """ Identify the vertices surrounding the area of interest """
    __tablename__ = 'prediction_model_grid_subsets'
    __table_args__ = (
        UniqueConstraint('prediction_model_id', 'geom'),
        {'comment': 'Identify the vertices surrounding the area of interest'}
    )

    id = Column(Integer, Sequence('prediction_model_grid_subsets_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Which model does this grid belong to? e.g. GDPS latlon.15x.15?
    prediction_model_id = Column(Integer, ForeignKey(
        'prediction_models.id'), nullable=False)
    prediction_model = relationship("PredictionModel")
    # Order of vertices is important!
    # 1st vertex top left, 2nd vertex top right, 3rd vertex bottom right, 4th vertex bottom left.
    geom = Column(Geometry('POLYGON'), nullable=False)


class ModelRunGridSubsetPrediction(Base):
    """ The prediction for a particular model grid subset.
    Each value is an array that corresponds to the vertex in the forecast bounding polygon. """
    __tablename__ = 'model_run_grid_subset_predictions'
    __table_args__ = (
        UniqueConstraint('prediction_model_run_id', 'prediction_model_grid_subset_id',
                         'prediction_timestamp'),
        {'comment': 'The prediction for a grid subset of a particular model run.'}
    )

    id = Column(Integer, Sequence('model_run_grid_subset_predictions_id_seq'),
                primary_key=True, nullable=False, index=True)
    # Which model run does this forecacst apply to? E.g. The GDPS 15x.15 run from 2020 07 07 12h00.
    prediction_model_run_id = Column(Integer, ForeignKey(
        'prediction_model_runs.id'), nullable=False)
    prediction_model_run = relationship(
        "PredictionModelRun", foreign_keys=[prediction_model_run_id])
    # Which grid does this forecast apply to?
    prediction_model_grid_subset_id = Column(Integer, ForeignKey(
        'prediction_model_grid_subsets.id'), nullable=False)
    prediction_model_grid_subset = relationship("PredictionModelGridSubset")
    # The date and time to which the forecast applies.
    prediction_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    # Temperature 2m above ground.
    tmp_tgl_2 = Column(ARRAY(Float), nullable=True)
    # Relative humidity 2m above ground.
    rh_tgl_2 = Column(ARRAY(Float), nullable=True)
