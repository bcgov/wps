"""Store the model surface elevation used at a station for a forecast run."""

from sqlalchemy import Column, Float, ForeignKey, Integer

from wps_shared.db.models import Base


class ModelRunStationElevation(Base):
    """Model surface height in metres for a station, shared by all hours in a forecast run.

    A null elevation means station metadata or a sampled surface value was unavailable.
    The model and initialization come from the associated forecast run.
    """

    __tablename__ = "model_run_station_elevations"

    prediction_model_run_timestamp_id = Column(
        Integer,
        ForeignKey("prediction_model_run_timestamps.id", ondelete="CASCADE"),
        primary_key=True,
    )
    station_code = Column(Integer, primary_key=True)
    elevation = Column(Float, nullable=True)
