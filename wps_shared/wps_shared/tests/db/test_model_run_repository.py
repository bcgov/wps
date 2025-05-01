import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from testcontainers.postgres import PostgresContainer
from wps_shared.db.crud.model_run_repository import ModelRunRepository

from wps_shared.db.models.weather_models import (
    PredictionModel,
    PredictionModelRunTimestamp,
    ProcessedModelRunUrl,
)

import os

from wps_shared.weather_models import ModelEnum, ProjectionEnum

os.environ["DOCKER_HOST"] = f"unix://{os.environ['HOME']}/.docker/run/docker.sock"


@pytest.fixture(scope="module")
def postgres_container():
    """Fixture to start a Postgres container."""
    with PostgresContainer("postgis/postgis:15-3.3") as postgres:
        yield postgres


@pytest.fixture
def db_session(postgres_container):
    """Fixture to provide a real SQLAlchemy session."""
    engine = create_engine(postgres_container.get_connection_url())
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        # Verify PostGIS installation
        result = connection.execute(text("SELECT postgis_full_version();"))
        print(result.fetchone())

    # Create tables for specific models under test
    PredictionModel.__table__.create(engine, checkfirst=True)
    PredictionModelRunTimestamp.__table__.create(engine, checkfirst=True)
    ProcessedModelRunUrl.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Make sure model exists
    session.add(PredictionModel(name="ECMWF Integrated Forecast System", abbreviation=ModelEnum.ECMWF.value, projection=ProjectionEnum.ECMWF_LATLON.value))
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def repository(db_session):
    """Fixture to provide the ModelRunRepository instance."""
    return ModelRunRepository(session=db_session)


def test_get_prediction_run(repository: ModelRunRepository, db_session: Session):
    prediction_model_id = 1
    prediction_run_timestamp = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

    # Insert a mock record
    mock_prediction_run = PredictionModelRunTimestamp(
        prediction_model_id=prediction_model_id,
        prediction_run_timestamp=prediction_run_timestamp,
        complete=False,
        interpolated=False,
    )
    db_session.add(mock_prediction_run)
    db_session.commit()

    result = repository.get_prediction_run(prediction_model_id, prediction_run_timestamp)

    assert result == mock_prediction_run


def test_get_prediction_model(repository: ModelRunRepository, db_session: Session):
    # Insert a mock record
    mock_prediction_model = PredictionModel(
        name="GFS Global Forecast System",
        abbreviation=ModelEnum.GFS.value,
        projection=ProjectionEnum.GFS_LONLAT.value,
    )
    db_session.add(mock_prediction_model)
    db_session.commit()

    result = repository.get_prediction_model(ModelEnum.GFS, ProjectionEnum.GFS_LONLAT)

    assert result == mock_prediction_model


def test_get_processed_file_record(repository: ModelRunRepository, db_session: Session):
    url = "http://example.com/file"

    # Insert a mock record
    mock_processed_file = ProcessedModelRunUrl(url=url, create_date=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc), update_date=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc))
    db_session.add(mock_processed_file)
    db_session.commit()

    result = repository.get_processed_file_record(url)

    assert result == mock_processed_file


def test_create_prediction_run(repository: ModelRunRepository):
    prediction_model_id = 1
    prediction_run_timestamp = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

    result = repository.create_prediction_run(prediction_model_id, prediction_run_timestamp)

    assert isinstance(result, PredictionModelRunTimestamp)
    assert result.prediction_model_id == prediction_model_id
    assert result.prediction_run_timestamp == prediction_run_timestamp

    stored_result = repository.get_prediction_run(prediction_model_id, prediction_run_timestamp)

    assert stored_result is not None
    assert stored_result == result
