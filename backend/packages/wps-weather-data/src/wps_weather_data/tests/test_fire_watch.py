from datetime import UTC, datetime

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.fire_watch import fetch_daily_run_predictions
from wps_weather_data.runs import RunsTable

RUN_TS = datetime(2026, 11, 17, 0, tzinfo=UTC)
LATER_RUN_TS = datetime(2026, 11, 17, 12, tzinfo=UTC)
DAY_1_1800 = datetime(2026, 11, 17, 18, tzinfo=UTC)
DAY_1_2000 = datetime(2026, 11, 17, 20, tzinfo=UTC)
DAY_2_2000 = datetime(2026, 11, 18, 20, tzinfo=UTC)
INGESTED_AT = datetime(2026, 11, 17, 6, tzinfo=UTC)


def make_rows(times, station_codes=(322,), temperature=10.0):
    return [
        {
            "station_code": code,
            "prediction_timestamp": time,
            "tmp_tgl_2": temperature,
            "rh_tgl_2": 50.0,
            "wind_tgl_10": 5.0,
            "wdir_tgl_10": 180.0,
            "bias_adjusted_temperature": temperature + 1,
            "bias_adjusted_rh": 51.0,
            "bias_adjusted_wind_speed": 6.0,
            "bias_adjusted_wdir": 181.0,
            "precip_24h": 4.0,
            "bias_adjusted_precip_24h": 4.5,
        }
        for code in station_codes
        for time in times
    ]


@pytest.fixture
def runs(tmp_path):
    return RunsTable(str(tmp_path / "runs"))


def test_no_table_gives_no_predictions(runs):
    assert fetch_daily_run_predictions(runs, ModelEnum.ECMWF, RUN_TS, 7, [322]) == []


def test_reads_the_run_at_2000_utc_for_the_stations(runs):
    runs.append_run(
        ModelEnum.ECMWF,
        RUN_TS,
        make_rows([DAY_2_2000, DAY_1_1800, DAY_1_2000], station_codes=(322, 209)),
        ingested_at=INGESTED_AT,
    )

    predictions = fetch_daily_run_predictions(runs, ModelEnum.ECMWF, RUN_TS, 7, [322])

    assert [(p.station_code, p.prediction_timestamp) for p in predictions] == [
        (322, DAY_1_2000),
        (322, DAY_2_2000),
    ]
    first = predictions[0]
    assert first.abbreviation == "ECMWF"
    assert first.prediction_run_timestamp == RUN_TS
    assert first.prediction_model_run_timestamp_id == 7
    assert first.update_date == INGESTED_AT
    assert (first.tmp_tgl_2, first.bias_adjusted_temperature) == (10.0, 11.0)
    assert (first.rh_tgl_2, first.bias_adjusted_rh) == (50.0, 51.0)
    assert (first.wind_tgl_10, first.bias_adjusted_wind_speed) == (5.0, 6.0)
    assert (first.wdir_tgl_10, first.bias_adjusted_wdir) == (180.0, 181.0)
    assert (first.precip_24h, first.bias_adjusted_precip_24h) == (4.0, 4.5)


def test_reads_only_the_requested_run_and_model(runs):
    runs.append_run(ModelEnum.ECMWF, RUN_TS, make_rows([DAY_1_2000], temperature=10.0))
    runs.append_run(ModelEnum.ECMWF, LATER_RUN_TS, make_rows([DAY_1_2000], temperature=20.0))
    runs.append_run(ModelEnum.GDPS, RUN_TS, make_rows([DAY_1_2000], temperature=30.0))

    predictions = fetch_daily_run_predictions(runs, ModelEnum.ECMWF, RUN_TS, 7, [322])

    assert [p.tmp_tgl_2 for p in predictions] == [10.0]


def test_a_reprocessed_run_gives_its_newest_values(runs):
    runs.append_run(
        ModelEnum.ECMWF,
        RUN_TS,
        make_rows([DAY_1_2000], temperature=10.0),
        ingested_at=INGESTED_AT,
    )
    runs.append_run(
        ModelEnum.ECMWF,
        RUN_TS,
        make_rows([DAY_1_2000], temperature=12.0),
        ingested_at=LATER_RUN_TS,
    )

    predictions = fetch_daily_run_predictions(runs, ModelEnum.ECMWF, RUN_TS, 7, [322])

    assert [p.tmp_tgl_2 for p in predictions] == [12.0]
