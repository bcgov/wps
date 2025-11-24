from datetime import datetime, timedelta, timezone

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_shared.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModel,
    PredictionModelRunTimestamp,
    ProcessedModelRunUrl,
    WeatherStationModelPrediction,
)
from wps_shared.weather_models import ModelEnum, ProjectionEnum

# Required for loading DOCKER_HOST
load_dotenv()


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
    WeatherStationModelPrediction.__table__.create(engine, checkfirst=True)
    session_ = sessionmaker(bind=engine, autoflush=False)
    session = session_()

    # Make sure model exists
    stmt = insert(PredictionModel).values(
        name="ECMWF Integrated Forecast System",
        abbreviation=ModelEnum.ECMWF.value,
        projection=ProjectionEnum.ECMWF_LATLON.value,
    )
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


def test_get_processed_file_record(repository: ModelRunRepository, db_session: Session):
    url = "https://example.com/file"

    # Insert a mock record
    mock_processed_file = ProcessedModelRunUrl(
        url=url, create_date=TEST_DATETIME, update_date=TEST_DATETIME
    )
    db_session.add(mock_processed_file)
    db_session.commit()

    result = repository.get_processed_url(url)

    assert result == mock_processed_file


def test_create_prediction_run(repository: ModelRunRepository):
    run_datetime = TEST_DATETIME + timedelta(hours=1)
    prediction_model_id = repository.get_prediction_model(
        ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON
    ).id
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
    created_run = repository.get_or_create_prediction_run(
        prediction_model, prediction_run_timestamp
    )

    # Verify the prediction run was created
    assert isinstance(created_run, PredictionModelRunTimestamp)
    assert created_run.prediction_model_id == prediction_model.id
    assert created_run.prediction_run_timestamp == prediction_run_timestamp

    # Verify the prediction run now exists in the database
    stored_run = repository.get_prediction_run(prediction_model.id, prediction_run_timestamp)
    assert stored_run is not None
    assert stored_run == created_run

    # Call the method again to ensure it retrieves the existing run
    retrieved_run = repository.get_or_create_prediction_run(
        prediction_model, prediction_run_timestamp
    )
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
    updated_prediction_run = repository.get_prediction_run(
        prediction_model.id, prediction_run_timestamp
    )
    assert updated_prediction_run is not None
    assert updated_prediction_run.complete is True


def test_store_model_run_prediction(repository: ModelRunRepository, db_session: Session):
    prediction_model = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON)
    prediction_run_timestamp = TEST_DATETIME + timedelta(hours=4)

    # Create a prediction run to associate with the prediction
    prediction_run = repository.get_or_create_prediction_run(
        prediction_model, prediction_run_timestamp
    )

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
    prediction_run = repository.get_or_create_prediction_run(
        prediction_model, prediction_run_timestamp
    )

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


@pytest.mark.parametrize(
    "mock_prediction_runs, complete, interpolated, expected",
    [
        # no prediction runs
        ([], False, False, 0),
        (
            [
                PredictionModelRunTimestamp(
                    prediction_model_id=1,
                    prediction_run_timestamp=TEST_DATETIME + timedelta(days=1, hours=1),
                    complete=False,
                    interpolated=False,
                )
            ],
            False,
            False,
            1,
        ),
        (
            [
                PredictionModelRunTimestamp(
                    prediction_model_id=1,
                    prediction_run_timestamp=TEST_DATETIME + timedelta(days=1, hours=2),
                    complete=True,
                    interpolated=False,
                )
            ],
            True,
            False,
            1,
        ),
        (
            [
                PredictionModelRunTimestamp(
                    prediction_model_id=1,
                    prediction_run_timestamp=TEST_DATETIME + timedelta(days=1, hours=3),
                    complete=False,
                    interpolated=True,
                )
            ],
            False,
            True,
            1,
        ),
        (
            [
                PredictionModelRunTimestamp(
                    prediction_model_id=1,
                    prediction_run_timestamp=TEST_DATETIME + timedelta(days=1, hours=4),
                    complete=True,
                    interpolated=True,
                )
            ],
            True,
            True,
            1,
        ),
    ],
)
def test_get_interpolated_prediction_value(
    mock_prediction_runs,
    complete,
    interpolated,
    expected,
    repository: ModelRunRepository,
    db_session: Session,
):
    # Clear the database before inserting mock data
    db_session.query(ModelRunPrediction).delete()
    db_session.query(PredictionModelRunTimestamp).delete()
    db_session.commit()

    # Insert mock prediction runs
    db_session.add_all(mock_prediction_runs)
    db_session.commit()

    results = repository.get_prediction_model_run_timestamp_records(
        model_type=ModelEnum.ECMWF,
        complete=complete,
        interpolated=interpolated,
    )

    assert len(results) == expected


def test_get_prediction_model(repository: ModelRunRepository, db_session: Session):
    # Insert a mock record
    mock_prediction_model = PredictionModel(
        name="GFS Global Forecast System",
        abbreviation=ModelEnum.GFS.value,
        projection=ProjectionEnum.GFS_LONLAT.value,
    )
    db_session.add(mock_prediction_model)
    db_session.commit()

    # Test retrieving the prediction model
    result = repository.get_prediction_model(ModelEnum.GFS, ProjectionEnum.GFS_LONLAT)

    assert result is not None
    assert result == mock_prediction_model
    assert result.name == "GFS Global Forecast System"
    assert result.abbreviation == ModelEnum.GFS.value
    assert result.projection == ProjectionEnum.GFS_LONLAT.value


def test_mark_url_as_processed_new_url(repository: ModelRunRepository, db_session: Session):
    url = "https://example.com/new_file"

    # Ensure the URL does not exist initially
    existing_url = repository.get_processed_url(url)
    assert existing_url is None

    # Call the method to mark the URL as processed
    repository.mark_url_as_processed(url)

    # Verify the URL is now stored in the database
    processed_url = repository.get_processed_url(url)
    assert processed_url is not None
    assert processed_url.url == url
    assert processed_url.create_date is not None
    assert processed_url.update_date is not None
    assert processed_url.create_date == processed_url.update_date


@pytest.mark.parametrize(
    "processed_urls, unprocessed_urls, expected_count, expected_model_run_complete",
    [
        (
            [
                ProcessedModelRunUrl(
                    url="https://example.com/file1",
                    create_date=TEST_DATETIME,
                    update_date=TEST_DATETIME,
                ),
                ProcessedModelRunUrl(
                    url="https://example.com/file2",
                    create_date=TEST_DATETIME,
                    update_date=TEST_DATETIME,
                ),
                ProcessedModelRunUrl(
                    url="https://example.com/file3",
                    create_date=TEST_DATETIME,
                    update_date=TEST_DATETIME,
                ),
            ],
            [],
            3,
            True,
        ),
        (
            [
                ProcessedModelRunUrl(
                    url="https://example.com/file1",
                    create_date=TEST_DATETIME,
                    update_date=TEST_DATETIME,
                ),
                ProcessedModelRunUrl(
                    url="https://example.com/file2",
                    create_date=TEST_DATETIME,
                    update_date=TEST_DATETIME,
                ),
            ],
            [
                ProcessedModelRunUrl(
                    url="https://example.com/file3",
                    create_date=TEST_DATETIME,
                    update_date=TEST_DATETIME,
                )
            ],
            2,
            False,
        ),
        ([], [], 0, False),
    ],
)
def test_get_processed_file_count(
    processed_urls,
    unprocessed_urls,
    expected_count,
    expected_model_run_complete,
    repository: ModelRunRepository,
    db_session: Session,
):
    # Ensure no records exist for the URLs
    db_session.query(ProcessedModelRunUrl).delete()
    db_session.commit()

    # Insert mock records for some of the URLs
    db_session.add_all(processed_urls)
    db_session.commit()

    urls = [url.url for url in processed_urls + unprocessed_urls]

    # Call the method to get the count of processed files
    processed_url_count = repository.get_processed_url_count(urls)

    # Verify the count matches the number of processed URLs
    assert processed_url_count == expected_count
    model_run_complete = repository.check_if_model_run_complete(urls)
    assert model_run_complete == expected_model_run_complete


def test_store_prediction_flushes_makes_record_queryable_immediately(
    repository: ModelRunRepository,
):
    prediction_model = repository.get_prediction_model(ModelEnum.ECMWF, ProjectionEnum.ECMWF_LATLON)
    run_timestamp = TEST_DATETIME + timedelta(hours=4)
    prediction_timestamp = TEST_DATETIME + timedelta(hours=10)

    # Create a prediction run to associate with the prediction
    prediction_run = repository.get_or_create_prediction_run(prediction_model, run_timestamp)

    prediction = WeatherStationModelPrediction(
        station_code=1,
        prediction_model_run_timestamp_id=prediction_run.id,
        prediction_timestamp=prediction_timestamp,
    )

    # should flush so the "stored" record is available for querying
    repository.store_weather_station_model_prediction(prediction)

    # query for the prediction before committing
    fetched_prediction = repository.get_weather_station_model_prediction(
        station_code=1,
        prediction_model_run_timestamp_id=prediction_run.id,
        prediction_timestamp=prediction_timestamp,
    )

    assert fetched_prediction is not None
    assert fetched_prediction == prediction
