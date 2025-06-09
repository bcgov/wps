from unittest import mock
import pytest
from datetime import datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, patch, create_autospec

from wps_shared.db.models.fire_watch import FireWatch, FireWatchWeather
from wps_shared.fuel_types import FuelTypeEnum
from app.fire_behaviour.prediction import FireBehaviourPrediction
from app.fire_watch.calculate_weather import (
    FIREWATCH_WEATHER_MODEL,
    calculate_fbp,
    check_prescription_status,
    gather_fire_watch_inputs,
    get_station_metadata,
    map_model_prediction_to_weather_indeterminate,
    process_all_fire_watch_weather,
    process_predictions,
    save_all_fire_watch_weather,
    validate_actual_weather_data,
    validate_fire_watch_inputs,
    validate_prediction_dates,
)
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation
from app.fire_watch.calculate_weather import MissingWeatherDataError


@pytest.fixture
def mock_fire_watch():
    return FireWatch(
        id=1,
        station_code=101,
        fuel_type=FuelTypeEnum.C3,
        temp_min=10,
        temp_max=30,
        rh_min=20,
        rh_max=60,
        wind_speed_min=5,
        wind_speed_max=20,
        ffmc_min=80,
        ffmc_max=95,
        dmc_min=10,
        dmc_max=30,
        dc_min=100,
        dc_max=300,
        isi_min=5,
        isi_max=15,
        bui_min=40,
        bui_max=80,
        hfi_min=0,
        hfi_max=4000,
        percent_grass_curing=0,
        percent_conifer=0,
        percent_dead_fir=0,
    )


@pytest.fixture
def mock_station_metadata():
    return WFWXWeatherStation(
        code=101,
        name="Test Station",
        lat=50.0,
        long=-120.0,
        elevation=500,
        wfwx_id="test_id",
        zone_code="test_zone",
    )


def generate_mock_predictions(prediction_timestamps):
    return [
        ModelPredictionDetails(
            station_code=101,
            abbreviation=FIREWATCH_WEATHER_MODEL.value,
            prediction_timestamp=timestamp,
            tmp_tgl_2=25,
            rh_tgl_2=40,
            precip_24h=0,
            wdir_tgl_10=180,
            wind_tgl_10=10,
            update_date=datetime(2025, 5, 4, tzinfo=timezone.utc),
            prediction_run_timestamp=datetime(2025, 5, 4, tzinfo=timezone.utc),
            prediction_model_run_timestamp_id=1,
        )
        for timestamp in prediction_timestamps
    ]


@pytest.fixture
def mock_predictions():
    prediction_timestamps = [
        datetime(2025, 5, 5, 20, tzinfo=timezone.utc),
        datetime(2025, 5, 6, 20, tzinfo=timezone.utc),
        datetime(2025, 5, 7, 20, tzinfo=timezone.utc),
        datetime(2025, 5, 8, 20, tzinfo=timezone.utc),
        datetime(2025, 5, 9, 20, tzinfo=timezone.utc),
        datetime(2025, 5, 10, 20, tzinfo=timezone.utc),
    ]
    return generate_mock_predictions(prediction_timestamps)


@pytest.fixture
def mock_actual_weather_data():
    return [
        WeatherIndeterminate(
            station_code=101,
            station_name="Test Station",
            latitude=50.0,
            longitude=-120.0,
            determinate=WeatherDeterminate.ACTUAL,
            utc_timestamp=datetime(2025, 5, 4, tzinfo=timezone.utc),
            temperature=25,
            relative_humidity=40,
            precipitation=0,
            wind_direction=180,
            wind_speed=10,
            fine_fuel_moisture_code=90,
            initial_spread_index=10,
            build_up_index=70,
            drought_code=200,
            duff_moisture_code=40,
        )
    ]


@pytest.fixture
def mock_fbp_result():
    return FireBehaviourPrediction(
        hfi=1000, ros=0.5, intensity_group=3, sixty_minute_fire_size=2.0, fire_type="Surface"
    )


@pytest.fixture
def mock_status_id_dict():
    return {"all": 1, "hfi": 2, "no": 3}


@pytest.mark.anyio
async def test_map_model_prediction_to_weather_indeterminate():
    model_prediction = ModelPredictionDetails(
        station_code=1,
        abbreviation=FIREWATCH_WEATHER_MODEL.value,
        prediction_timestamp=datetime(2025, 4, 25, 20, tzinfo=timezone.utc),
        tmp_tgl_2=25.0,
        rh_tgl_2=50.0,
        precip_24h=5.0,
        wdir_tgl_10=180.0,
        wind_tgl_10=10.0,
        update_date=datetime(2025, 4, 25, 14, tzinfo=timezone.utc),
        prediction_run_timestamp=datetime(2025, 4, 25, 12, tzinfo=timezone.utc),
        prediction_model_run_timestamp_id=1234,
    )
    station_details = WFWXWeatherStation(
        code=1, name="Station 1", lat=50.0, long=-120.0, elevation=1, wfwx_id="1", zone_code=None
    )
    result = map_model_prediction_to_weather_indeterminate(model_prediction, station_details)
    assert result.station_code == 1
    assert result.station_name == "Station 1"
    assert result.temperature == pytest.approx(25.0)
    assert result.relative_humidity == pytest.approx(50.0)
    assert result.precipitation == pytest.approx(5.0)
    assert result.wind_direction == pytest.approx(180.0)
    assert result.wind_speed == pytest.approx(10.0)
    assert result.utc_timestamp == datetime(2025, 4, 25, 20, tzinfo=timezone.utc)
    assert result.update_date == datetime(2025, 4, 25, 14, tzinfo=timezone.utc)
    assert result.prediction_run_timestamp == datetime(2025, 4, 25, 12, tzinfo=timezone.utc)


@pytest.mark.anyio
@patch("app.fire_watch.calculate_weather.get_auth_header", new_callable=AsyncMock)
@patch(
    "app.fire_watch.calculate_weather.get_wfwx_stations_from_station_codes", new_callable=AsyncMock
)
async def test_fetch_station_metadata(mock_get_stations, mock_get_auth_header):
    mock_get_stations.return_value = [
        WFWXWeatherStation(
            code=1,
            name="Station 1",
            lat=50.0,
            long=-120.0,
            elevation=1,
            wfwx_id="1",
            zone_code=None,
        )
    ]
    result = await get_station_metadata([1])
    assert result[1].name == "Station 1"


@pytest.mark.anyio
async def test_gather_fire_watch_inputs(
    mocker, mock_fire_watch, mock_predictions, mock_actual_weather_data
):
    mock_session = AsyncMock()
    mocker.patch(
        "app.fire_watch.calculate_weather.get_latest_daily_model_prediction_for_stations",
        return_value=mock_predictions,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_actuals_and_forecasts",
        return_value=(mock_actual_weather_data, []),
    )

    predictions, actual_weather_data = await gather_fire_watch_inputs(
        mock_session, mock_fire_watch, 1
    )

    assert predictions == mock_predictions
    assert actual_weather_data == mock_actual_weather_data


def test_validate_fire_watch_inputs(
    mock_fire_watch, mock_station_metadata, mock_actual_weather_data
):
    result = validate_fire_watch_inputs(
        mock_fire_watch,
        mock_station_metadata,
        mock_actual_weather_data,
    )
    assert result is True


def test_validate_fire_watch_inputs_raises_missing_station_metadata(
    mock_fire_watch, mock_actual_weather_data
):
    # Should raise MissingWeatherDataError if station_metadata is None
    with pytest.raises(MissingWeatherDataError) as exc:
        validate_fire_watch_inputs(mock_fire_watch, None, mock_actual_weather_data)
    assert f"Missing station metadata for station {mock_fire_watch.station_code}" in str(exc.value)


def test_validate_fire_watch_inputs_raises_invalid_actual_weather_data(
    mock_fire_watch, mock_station_metadata, mock_actual_weather_data
):
    # Should raise MissingWeatherDataError if actual_weather_data is invalid
    # Invalidate actual_weather_data
    mock_actual_weather_data[0].duff_moisture_code = None
    with pytest.raises(MissingWeatherDataError) as exc:
        validate_fire_watch_inputs(mock_fire_watch, mock_station_metadata, mock_actual_weather_data)
    assert f"Invalid actual weather data for station {mock_fire_watch.station_code}" in str(
        exc.value
    )


def test_validate_actual_weather_data(mock_actual_weather_data):
    result = validate_actual_weather_data(mock_actual_weather_data)
    assert result is True


def test_validate_actual_weather_data_fails(mock_actual_weather_data):
    mock_actual_weather_data[0].duff_moisture_code = None
    result = validate_actual_weather_data(mock_actual_weather_data)
    assert result is False


def test_validate_prediction_dates(mock_predictions):
    result = validate_prediction_dates(
        mock_predictions,
        datetime(2025, 5, 5, tzinfo=timezone.utc),
        datetime(2025, 5, 10, tzinfo=timezone.utc),
    )
    assert result is True


def test_validate_prediction_dates_fails(mock_predictions):
    result = validate_prediction_dates(
        mock_predictions,
        datetime(2025, 5, 5, tzinfo=timezone.utc),
        datetime(2025, 5, 11, tzinfo=timezone.utc),
    )
    assert result is False


def test_calculate_fbp(mock_fire_watch, mock_station_metadata, mock_actual_weather_data):
    result = calculate_fbp(mock_fire_watch, mock_station_metadata, mock_actual_weather_data[0])
    assert result.hfi == pytest.approx(3350, abs=10)


def test_check_prescription_status_all(mock_fire_watch, mock_status_id_dict):
    mock_weather = FireWatchWeather(
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        ffmc=85,
        dmc=20,
        dc=200,
        isi=10,
        bui=50,
        hfi=1000,
    )
    result = check_prescription_status(mock_fire_watch, mock_weather, mock_status_id_dict)
    assert result == 1


def test_check_prescription_status_hfi(mock_fire_watch, mock_status_id_dict):
    mock_weather = FireWatchWeather(
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        ffmc=99,
        dmc=20,
        dc=200,
        isi=10,
        bui=50,
        hfi=1000,
    )
    result = check_prescription_status(mock_fire_watch, mock_weather, mock_status_id_dict)
    assert result == 2


def test_check_prescription_status_none(mock_fire_watch, mock_status_id_dict):
    mock_weather = FireWatchWeather(
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        ffmc=99,
        dmc=20,
        dc=200,
        isi=10,
        bui=50,
        hfi=5000,
    )
    result = check_prescription_status(mock_fire_watch, mock_weather, mock_status_id_dict)
    assert result == 3


@pytest.mark.anyio
async def test_process_predictions(
    mock_fire_watch,
    mock_station_metadata,
    mock_predictions,
    mock_actual_weather_data,
    mock_status_id_dict,
    mock_fbp_result,
    mocker,
):
    mocker.patch(
        "app.fire_watch.calculate_weather.map_model_prediction_to_weather_indeterminate",
        side_effect=lambda p, s: mock_actual_weather_data[0],
    )
    mocker.patch("app.fire_watch.calculate_weather.calculate_fbp", return_value=mock_fbp_result)

    result = await process_predictions(
        mock_fire_watch,
        mock_station_metadata,
        mock_predictions,
        mock_actual_weather_data,
        mock_status_id_dict,
        1,
    )
    assert len(result) == 6
    assert result[0].hfi == 1000


@pytest.mark.anyio
async def test_process_all_fire_watch_weather_skips_if_weather_exists(mocker, mock_fire_watch):
    mock_fire_weather = create_autospec(FireWatchWeather)
    mock_fire_weather.fire_watch_id = mock_fire_watch.id
    mocker.patch(
        "app.fire_watch.calculate_weather.get_latest_prediction_timestamp_id_for_model",
        return_value=1,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_fire_watch_weather_by_model_run_parameter_id",
        return_value=[
            mock_fire_weather
        ],  # Simulate that weather data does not exist for a FireWatch
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_all_fire_watches",
        return_value=[(mock_fire_watch, None)],
    )
    mock_get_station_metadata = mocker.patch(
        "app.fire_watch.calculate_weather.get_station_metadata"
    )
    mock_get_all_prescription_status = mocker.patch(
        "app.fire_watch.calculate_weather.get_all_prescription_status"
    )
    mock_process_single_fire_watch = mocker.patch(
        "app.fire_watch.calculate_weather.process_single_fire_watch"
    )

    start_date = datetime(2025, 5, 5, tzinfo=timezone.utc)
    await process_all_fire_watch_weather(start_date)

    # mock_get_all_fire_watches.assert_not_called()
    mock_get_station_metadata.assert_not_called()
    mock_get_all_prescription_status.assert_not_called()
    mock_process_single_fire_watch.assert_not_called()


@pytest.mark.anyio
async def test_process_all_fire_watch_weather_processes_fire_watches(
    mocker, mock_fire_watch, mock_status_id_dict, mock_station_metadata
):
    mock_fire_weather = create_autospec(FireWatchWeather)
    mock_fire_weather.fire_watch_id = mock_fire_watch.id
    mocker.patch(
        "app.fire_watch.calculate_weather.get_latest_prediction_timestamp_id_for_model",
        return_value=1,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_fire_watch_weather_by_model_run_parameter_id",
        return_value=[],  # Simulate that weather data does not exist for a FireWatch
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_all_fire_watches",
        return_value=[(mock_fire_watch, None)],
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_station_metadata",
        return_value={101: mock_station_metadata},
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_all_prescription_status",
        return_value=mock_status_id_dict,
    )
    mock_process_single_fire_watch = mocker.patch(
        "app.fire_watch.calculate_weather.process_single_fire_watch", AsyncMock()
    )

    start_date = datetime(2025, 5, 5, tzinfo=timezone.utc)
    await process_all_fire_watch_weather(start_date)

    mock_process_single_fire_watch.assert_called_once_with(
        mock.ANY,
        mock_fire_watch,
        {101: mock_station_metadata},
        mock_status_id_dict,
        1,
    )


@pytest.mark.anyio
async def test_save_all_fire_watch_weather_adds_new_records(mocker):
    mock_session = AsyncMock()
    mock_record = create_autospec(FireWatchWeather)
    mock_record.fire_watch_id = 1
    mock_record.date = "2025-05-05"
    mock_record.prediction_model_run_timestamp_id = 123

    # Simulate no existing record found
    mock_execute = AsyncMock()
    mock_execute.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_execute

    mocker.patch.object(FireWatchWeather, "UPDATABLE_FIELDS", ["temperature", "hfi"])

    await save_all_fire_watch_weather(mock_session, [mock_record])

    mock_session.execute.assert_awaited_once()
    mock_session.add.assert_called_once_with(mock_record)


@pytest.mark.anyio
async def test_save_all_fire_watch_weather_updates_existing_records(mocker):
    mock_session = AsyncMock()
    mock_record = create_autospec(FireWatchWeather)
    mock_record.fire_watch_id = 1
    mock_record.date = "2025-05-05"
    mock_record.prediction_model_run_timestamp_id = 123
    mock_record.temperature = 25
    mock_record.hfi = 1000

    # Simulate existing record found
    existing_record = create_autospec(FireWatchWeather)
    mock_execute = AsyncMock()
    mock_execute.scalar_one_or_none.return_value = existing_record
    mock_session.execute.return_value = mock_execute

    mocker.patch.object(FireWatchWeather, "UPDATABLE_FIELDS", ["temperature", "hfi"])

    await save_all_fire_watch_weather(mock_session, [mock_record])

    mock_session.execute.assert_awaited_once()
    # Should not add new record
    mock_session.add.assert_not_called()
    # Should update fields
    assert existing_record.temperature == mock_record.temperature
    assert existing_record.hfi == mock_record.hfi


@pytest.mark.anyio
async def test_save_all_fire_watch_weather_handles_multiple_records(mocker):
    mock_session = AsyncMock()
    mock_record1 = create_autospec(FireWatchWeather)
    mock_record2 = create_autospec(FireWatchWeather)
    mock_record1.fire_watch_id = 1
    mock_record2.fire_watch_id = 2
    mock_record1.date = mock_record2.date = "2025-05-05"
    mock_record1.prediction_model_run_timestamp_id = 123
    mock_record2.prediction_model_run_timestamp_id = 124

    # First record: no existing, second: existing
    existing_record2 = create_autospec(FireWatchWeather)
    mock_execute1 = AsyncMock()
    mock_execute1.scalar_one_or_none.return_value = None
    mock_execute2 = AsyncMock()
    mock_execute2.scalar_one_or_none.return_value = existing_record2
    mock_session.execute.side_effect = [mock_execute1, mock_execute2]

    mocker.patch.object(FireWatchWeather, "UPDATABLE_FIELDS", ["temperature"])

    await save_all_fire_watch_weather(mock_session, [mock_record1, mock_record2])

    assert mock_session.add.call_count == 1
    assert mock_session.add.call_args[0][0] == mock_record1
    assert existing_record2.temperature == mock_record2.temperature
