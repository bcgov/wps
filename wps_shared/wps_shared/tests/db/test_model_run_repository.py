import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert
from testcontainers.postgres import PostgresContainer
from wps_shared.db.crud.model_run_repository import ModelRunRepository

from wps_shared.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModel,
    PredictionModelRunTimestamp,
    ProcessedModelRunUrl,
)

from dotenv import load_dotenv

# Required for loading DOCKER_HOST
load_dotenv()

from wps_shared.weather_models import ModelEnum, ProjectionEnum

TEST_DATETIME = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)


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
    ModelRunPrediction.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Make sure model exists
    stmt = insert(PredictionModel).values(name="ECMWF Integrated Forecast System", abbreviation=ModelEnum.ECMWF.value, projection=ProjectionEnum.ECMWF_LATLON.value)
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
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

    # Insert a mock record
    mock_prediction_run = PredictionModelRunTimestamp(
        prediction_model_id=prediction_model_id,
        prediction_run_timestamp=TEST_DATETIME,
        complete=False,
        interpolated=False,
    )
    db_session.add(mock_prediction_run)
    db_session.commit()

    result = repository.get_prediction_run(prediction_model_id, TEST_DATETIME)

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
    mock_processed_file = ProcessedModelRunUrl(url=url, create_date=TEST_DATETIME, update_date=TEST_DATETIME)
    db_session.add(mock_processed_file)
    db_session.commit()

    result = repository.get_processed_file_record(url)

    assert result == mock_processed_file


def test_create_prediction_run(repository: ModelRunRepository):
    run_datetime = TEST_DATETIME + timedelta(hours=1)
    prediction_model_id = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON).id
    result = repository.create_prediction_run(prediction_model_id, run_datetime)

    assert isinstance(result, PredictionModelRunTimestamp)
    assert result.prediction_model_id == prediction_model_id
    assert result.prediction_run_timestamp == run_datetime

    stored_result = repository.get_prediction_run(prediction_model_id, run_datetime)

    assert stored_result is not None
    assert stored_result == result

def test_get_or_create_prediction_run(repository: ModelRunRepository, db_session: Session):
    prediction_model = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON)
    prediction_run_timestamp = TEST_DATETIME + timedelta(hours=2)

    # Ensure no prediction run exists initially
    existing_run = repository.get_prediction_run(prediction_model.id, prediction_run_timestamp)
    assert existing_run is None

    # Call the method to get or create the prediction run
    created_run = repository.get_or_create_prediction_run(prediction_model, prediction_run_timestamp)

    # Verify the prediction run was created
    assert isinstance(created_run, PredictionModelRunTimestamp)
    assert created_run.prediction_model_id == prediction_model.id
    assert created_run.prediction_run_timestamp == prediction_run_timestamp

    # Verify the prediction run now exists in the database
    stored_run = repository.get_prediction_run(prediction_model.id, prediction_run_timestamp)
    assert stored_run is not None
    assert stored_run == created_run

    # Call the method again to ensure it retrieves the existing run
    retrieved_run = repository.get_or_create_prediction_run(prediction_model, prediction_run_timestamp)
    assert retrieved_run == created_run

def test_mark_prediction_model_run_processed(repository: ModelRunRepository, db_session: Session):
    prediction_model = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON)
    prediction_run_timestamp = TEST_DATETIME + timedelta(hours=3)
    # Insert a mock prediction run
    mock_prediction_run = PredictionModelRunTimestamp(
        prediction_model_id=prediction_model.id,
        prediction_run_timestamp=prediction_run_timestamp,
        complete=False,
        interpolated=False,
    )
    db_session.add(mock_prediction_run)
    db_session.commit()

    # Call the method to mark the prediction run as processed
    repository.mark_prediction_model_run_processed(
        model=ModelEnum.ECMWF,
        projection=ProjectionEnum.ECMWF_LATLON,
        model_run_datetime=prediction_run_timestamp,
    )

    # Verify the prediction run is marked as complete
    updated_prediction_run = repository.get_prediction_run(prediction_model.id, prediction_run_timestamp)
    assert updated_prediction_run is not None
    assert updated_prediction_run.complete is True

def test_store_model_run_prediction(repository: ModelRunRepository, db_session: Session):
    prediction_model = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON)
    prediction_run_timestamp = TEST_DATETIME + timedelta(hours=4)

    # Create a prediction run to associate with the prediction
    prediction_run = repository.get_or_create_prediction_run(prediction_model, prediction_run_timestamp)

    # Create a mock prediction
    mock_prediction = ModelRunPrediction(
        prediction_model_run_timestamp_id=prediction_run.id,
        prediction_timestamp=TEST_DATETIME + timedelta(hours=5),
        station_code=12345,
    )

    # Call the method to store the prediction
    repository.store_model_run_prediction(mock_prediction)

    # Verify the prediction is stored in the database
    stored_prediction = repository.get_model_run_prediction(
        prediction_run=prediction_run,
        prediction_timestamp=mock_prediction.prediction_timestamp,
        station_code=mock_prediction.station_code,
    )

    assert stored_prediction is not None
    assert stored_prediction == mock_prediction

def test_get_model_run_predictions_for_station(repository: ModelRunRepository, db_session: Session):
    prediction_model = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON)
    prediction_run_timestamp = TEST_DATETIME + timedelta(hours=6)

    # Create a prediction run to associate with the predictions
    prediction_run = repository.get_or_create_prediction_run(prediction_model, prediction_run_timestamp)

    # Insert mock predictions
    mock_predictions = [
        ModelRunPrediction(
            prediction_model_run_timestamp_id=prediction_run.id,
            prediction_timestamp=TEST_DATETIME + timedelta(hours=i),
            station_code=12345,
        )
        for i in range(3)
    ]
    db_session.add_all(mock_predictions)
    db_session.commit()

    # Call the method to get predictions for the station
    predictions = repository.get_model_run_predictions_for_station(
        station_code=12345,
        prediction_run=prediction_run,
    )

    # Verify the predictions are retrieved and ordered correctly
    assert predictions is not None
    assert len(predictions) == len(mock_predictions)
    for i, prediction in enumerate(predictions):
        assert prediction == mock_predictions[i]






