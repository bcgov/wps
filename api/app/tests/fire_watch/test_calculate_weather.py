from unittest import mock
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, create_autospec

from wps_shared.db.models.fire_watch import FireWatch, FireWatchWeather
from wps_shared.fuel_types import FuelTypeEnum
from app.fire_behaviour.prediction import FireBehaviourPrediction
from app.fire_watch.calculate_weather import (
    FIREWATCH_WEATHER_MODEL,
    calculate_fbp,
    check_optional_fwi_fields,
    check_prescription_status,
    gather_fire_watch_inputs,
    get_station_metadata,
    in_range,
    map_model_prediction_to_weather_indeterminate,
    process_all_fire_watch_weather,
    process_predictions,
    process_single_fire_watch,
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
def mock_partial_fire_watch():
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
        # no ffmc
        dmc_min=10,
        dmc_max=30,
        dc_min=100,
        dc_max=300,
        isi_min=5,
        isi_max=15,
        # no bui
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


@pytest.fixture
def mock_single_model_prediction():
    return ModelPredictionDetails(
        station_code=1,
        abbreviation=FIREWATCH_WEATHER_MODEL.value,
        prediction_timestamp=datetime(2025, 4, 25, 20, tzinfo=timezone.utc),
        tmp_tgl_2=20.0,
        rh_tgl_2=55.0,
        precip_24h=5.0,
        wdir_tgl_10=90.0,
        wind_tgl_10=7.0,
        bias_adjusted_wind_speed=10.0,
        bias_adjusted_wdir=180.0,
        bias_adjusted_rh=50.0,
        bias_adjusted_temperature=25.0,
        update_date=datetime(2025, 4, 25, 14, tzinfo=timezone.utc),
        prediction_run_timestamp=datetime(2025, 4, 25, 12, tzinfo=timezone.utc),
        prediction_model_run_timestamp_id=1234,
    )


@pytest.mark.anyio
async def test_map_model_prediction_to_weather_indeterminate_bias_values(
    mock_station_metadata, mock_single_model_prediction
):
    model_prediction = mock_single_model_prediction

    # if all bias-adjusted values are present, they should be used
    result = map_model_prediction_to_weather_indeterminate(model_prediction, mock_station_metadata)
    assert result.station_code == 1
    assert result.station_name == "Test Station"
    assert result.temperature == pytest.approx(25.0)
    assert result.relative_humidity == pytest.approx(50.0)
    assert result.precipitation == pytest.approx(5.0)
    assert result.wind_direction == pytest.approx(180.0)
    assert result.wind_speed == pytest.approx(10.0)
    assert result.utc_timestamp == datetime(2025, 4, 25, 20, tzinfo=timezone.utc)
    assert result.update_date == datetime(2025, 4, 25, 14, tzinfo=timezone.utc)
    assert result.prediction_run_timestamp == datetime(2025, 4, 25, 12, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_map_model_prediction_to_weather_indeterminate_missing_bias_value(
    mock_station_metadata, mock_single_model_prediction
):
    model_prediction = mock_single_model_prediction
    model_prediction.bias_adjusted_wind_speed = None

    # if a bias-adjusted value is missing, the non-bias values should be used for all params
    result = map_model_prediction_to_weather_indeterminate(model_prediction, mock_station_metadata)
    assert result.station_code == 1
    assert result.station_name == "Test Station"
    assert result.temperature == pytest.approx(20.0)
    assert result.relative_humidity == pytest.approx(55.0)
    assert result.precipitation == pytest.approx(5.0)
    assert result.wind_direction == pytest.approx(90.0)
    assert result.wind_speed == pytest.approx(7.0)
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


@pytest.mark.parametrize("fire_watch_name", ["mock_fire_watch", "mock_partial_fire_watch"])
def test_check_prescription_status_all(request, fire_watch_name, mock_status_id_dict):
    fire_watch = request.getfixturevalue(fire_watch_name)
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
    result = check_prescription_status(fire_watch, mock_weather, mock_status_id_dict)
    assert result == 1


@pytest.mark.parametrize(
    ("fire_watch_name", "expected_result"),
    [
        ("mock_fire_watch", 2),
        ("mock_partial_fire_watch", 1),
    ],
)
def test_check_prescription_status_hfi(
    request, fire_watch_name, expected_result, mock_status_id_dict
):
    fire_watch = request.getfixturevalue(fire_watch_name)
    mock_weather = FireWatchWeather(
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        ffmc=99,  # ffmc is out of range for mock_fire_watch, but not a required check for mock_partial_fire_watch
        dmc=20,
        dc=200,
        isi=10,
        bui=50,
        hfi=1000,
    )
    result = check_prescription_status(fire_watch, mock_weather, mock_status_id_dict)
    assert result == expected_result


@pytest.mark.parametrize("fire_watch_name", ["mock_fire_watch", "mock_partial_fire_watch"])
def test_check_prescription_status_none(request, fire_watch_name, mock_status_id_dict):
    fire_watch = request.getfixturevalue(fire_watch_name)
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
    result = check_prescription_status(fire_watch, mock_weather, mock_status_id_dict)
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
    mocker.patch(
        "app.fire_watch.calculate_weather.get_latest_prediction_timestamp_id_for_model",
        return_value=1,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_fire_watches_missing_weather_for_run",
        return_value=[],
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

    await process_all_fire_watch_weather()

    mock_get_station_metadata.assert_not_called()
    mock_get_all_prescription_status.assert_not_called()
    mock_process_single_fire_watch.assert_not_called()


@pytest.mark.anyio
async def test_process_all_fire_watch_weather_processes_fire_watches(
    mocker, mock_fire_watch, mock_status_id_dict, mock_station_metadata
):
    mocker.patch(
        "app.fire_watch.calculate_weather.get_latest_prediction_timestamp_id_for_model",
        return_value=1,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.get_fire_watches_missing_weather_for_run",
        return_value=[mock_fire_watch],
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

    await process_all_fire_watch_weather()

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
    mocker.patch(
        "app.fire_watch.calculate_weather.get_fire_watch_weather_by_fire_watch_id_and_model_run",
        return_value=None,
    )

    mocker.patch.object(FireWatchWeather, "UPDATABLE_FIELDS", ["temperature", "hfi"])

    await save_all_fire_watch_weather(mock_session, [mock_record])

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
    existing_record.date = "2025-05-05"
    mocker.patch(
        "app.fire_watch.calculate_weather.get_fire_watch_weather_by_fire_watch_id_and_model_run",
        return_value=[existing_record],
    )

    mocker.patch.object(FireWatchWeather, "UPDATABLE_FIELDS", ["temperature", "hfi"])

    await save_all_fire_watch_weather(mock_session, [mock_record])

    # Should not add new record
    mock_session.add.assert_not_called()
    # Should update fields
    assert existing_record.temperature == mock_record.temperature
    assert existing_record.hfi == mock_record.hfi


@pytest.mark.anyio
async def test_process_single_fire_watch_success(
    mocker, mock_fire_watch, mock_station_metadata, mock_status_id_dict
):
    mock_session = AsyncMock()
    wfwx_station_map = {mock_fire_watch.station_code: mock_station_metadata}
    prediction_run_timestamp_id = 1

    mock_predictions = ["predictions"]
    mock_actual_weather_data = ["actuals"]
    mock_fire_watch_predictions = ["fw_weather"]

    mocker.patch(
        "app.fire_watch.calculate_weather.gather_fire_watch_inputs",
        AsyncMock(return_value=(mock_predictions, mock_actual_weather_data)),
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.validate_fire_watch_inputs",
        return_value=True,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.process_predictions",
        AsyncMock(return_value=mock_fire_watch_predictions),
    )
    mock_save = mocker.patch(
        "app.fire_watch.calculate_weather.save_all_fire_watch_weather",
        AsyncMock(),
    )
    mock_logger = mocker.patch("app.fire_watch.calculate_weather.logger")

    await process_single_fire_watch(
        mock_session,
        mock_fire_watch,
        wfwx_station_map,
        mock_status_id_dict,
        prediction_run_timestamp_id,
    )

    mock_save.assert_awaited_once_with(mock_session, mock_fire_watch_predictions)
    mock_logger.info.assert_called()  # Should log save info


@pytest.mark.anyio
async def test_process_single_fire_watch_missing_station_metadata(
    mocker, mock_fire_watch, mock_status_id_dict
):
    mock_session = AsyncMock()
    wfwx_station_map = {}  # No station metadata
    prediction_run_timestamp_id = 1

    mock_logger = mocker.patch("app.fire_watch.calculate_weather.logger")

    result = await process_single_fire_watch(
        mock_session,
        mock_fire_watch,
        wfwx_station_map,
        mock_status_id_dict,
        prediction_run_timestamp_id,
    )

    assert result is None
    mock_logger.warning.assert_called_once()
    assert "Missing station metadata" in mock_logger.warning.call_args[0][0]


@pytest.mark.anyio
async def test_process_single_fire_watch_invalid_inputs(
    mocker, mock_fire_watch, mock_station_metadata, mock_status_id_dict
):
    mock_session = AsyncMock()
    wfwx_station_map = {mock_fire_watch.station_code: mock_station_metadata}
    prediction_run_timestamp_id = 1

    mocker.patch(
        "app.fire_watch.calculate_weather.gather_fire_watch_inputs",
        AsyncMock(return_value=(["predictions"], ["actuals"])),
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.validate_fire_watch_inputs",
        return_value=False,
    )

    with pytest.raises(ValueError) as exc:
        await process_single_fire_watch(
            mock_session,
            mock_fire_watch,
            wfwx_station_map,
            mock_status_id_dict,
            prediction_run_timestamp_id,
        )
    assert f"Invalid inputs for FireWatch {mock_fire_watch.id}" in str(exc.value)


@pytest.mark.anyio
async def test_process_single_fire_watch_no_predictions_to_save(
    mocker, mock_fire_watch, mock_station_metadata, mock_status_id_dict
):
    mock_session = AsyncMock()
    wfwx_station_map = {mock_fire_watch.station_code: mock_station_metadata}
    prediction_run_timestamp_id = 1

    mocker.patch(
        "app.fire_watch.calculate_weather.gather_fire_watch_inputs",
        AsyncMock(return_value=(["predictions"], ["actuals"])),
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.validate_fire_watch_inputs",
        return_value=True,
    )
    mocker.patch(
        "app.fire_watch.calculate_weather.process_predictions",
        AsyncMock(return_value=[]),
    )
    mock_save = mocker.patch(
        "app.fire_watch.calculate_weather.save_all_fire_watch_weather",
        AsyncMock(),
    )
    mock_logger = mocker.patch("app.fire_watch.calculate_weather.logger")

    await process_single_fire_watch(
        mock_session,
        mock_fire_watch,
        wfwx_station_map,
        mock_status_id_dict,
        prediction_run_timestamp_id,
    )

    mock_save.assert_not_called()
    # Should not log save info
    assert not any(
        "Saved" in str(call) for call in [c[0][0] for c in mock_logger.info.call_args_list]
    )


def test_check_optional_fwi_fields_all_fields_in_range(mock_fire_watch):
    # Weather values within range
    weather = FireWatchWeather(
        ffmc=85,
        dmc=20,
        dc=100,
        isi=14,
        bui=60,
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        hfi=1000,
    )
    result = check_optional_fwi_fields(mock_fire_watch, weather)
    assert result == dict.fromkeys(FireWatch.OPTIONAL_FWI_FIELDS, True)


def test_check_optional_fwi_fields_some_fields_out_of_range(mock_fire_watch):
    mock_fire_watch.ffmc_min = 80
    mock_fire_watch.ffmc_max = 90
    mock_fire_watch.dmc_min = 10
    mock_fire_watch.dmc_max = 30
    mock_fire_watch.dc_min = 100
    mock_fire_watch.dc_max = 200
    weather = FireWatchWeather(
        ffmc=95,  # out of range
        dmc=20,  # in range
        dc=90,  # out of range
        isi=14,  # in range
        bui=60,  # in range
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        hfi=1000,
    )
    result = check_optional_fwi_fields(mock_fire_watch, weather)
    assert result == {"ffmc": False, "dmc": True, "dc": False, "isi": True, "bui": True}


def test_check_optional_fwi_fields_missing_min_max(mock_fire_watch):
    # ffmc/dmc not required for this fire watch
    mock_fire_watch.ffmc_min = None
    mock_fire_watch.ffmc_max = None
    mock_fire_watch.dmc_min = None
    mock_fire_watch.dmc_max = None
    weather = FireWatchWeather(
        ffmc=95,  # not required
        dmc=20,  # not required
        dc=90,  # out of range
        isi=15,  # in range
        bui=60,  # in range
        temperature=25,
        relative_humidity=40,
        wind_speed=10,
        hfi=1000,
    )
    result = check_optional_fwi_fields(mock_fire_watch, weather)
    assert result == {"isi": True, "bui": True, "dc": False}


@pytest.mark.parametrize(
    "val, min_val, max_val, expected",
    [
        (5, 1, 10, True),  # value within range
        (1, 1, 10, True),  # value equal to min
        (10, 1, 10, True),  # value equal to max
        (0, 1, 10, False),  # value below min
        (11, 1, 10, False),  # value above max
        (5.5, 1.0, 10.0, True),  # float within range
        (1.0, 1.0, 10.0, True),  # float equal to min
        (10.0, 1.0, 10.0, True),  # float equal to max
        (0.9, 1.0, 10.0, False),  # float below min
        (10.1, 1.0, 10.0, False),  # float above max
    ],
)
def test_in_range(val, min_val, max_val, expected):
    assert in_range(val, min_val, max_val) is expected
