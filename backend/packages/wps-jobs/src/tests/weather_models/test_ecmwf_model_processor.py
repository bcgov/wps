from datetime import datetime, timezone

import pytest
import wps_nwp as nwp
from weather_model_jobs.ecmwf_model_processor import VARIABLES, station_values
from wps_nwp.tests.fakes import real_grib
from wps_shared.db.models.weather_models import ModelRunPrediction

RUN = datetime(2024, 10, 10, 0, tzinfo=timezone.utc)

# Two stations, each sitting on a point of the grid the fields below are on.
STATION_LATS = [50.0, 50.0]
STATION_LONS = [10.0, 10.25]


def field(variable: nwp.Variable, short_name: str, values) -> nwp.Field:
    """An ECMWF field on a 2x2 grid whose top row is at 50N, from 10E to 10.25E."""
    grib = real_grib(values, short_name=short_name, first_lat=50.0, first_lon=10.0, spacing=0.25)
    return nwp.Field("ifs", variable, RUN, 3, "mock_grib_url", grib)


@pytest.fixture
def fields():
    return [
        field(nwp.Variable.T2M, "2t", [[273.15, 283.15], [273.17, 273.18]]),
        field(nwp.Variable.D2M, "2d", [[273.15, 273.15], [273.17, 273.18]]),
        field(nwp.Variable.U10, "10u", [[5.0, 0.0], [4.9, 5.0]]),
        field(nwp.Variable.V10, "10v", [[3.0, -10.0], [2.9, 3.0]]),
        field(nwp.Variable.PRECIP, "tp", [[0.2, 0.0], [0.2, 0.23]]),
    ]


def test_variables_are_what_the_stored_values_are_derived_from():
    assert set(VARIABLES) == {
        nwp.Variable.T2M,
        nwp.Variable.D2M,
        nwp.Variable.U10,
        nwp.Variable.V10,
        nwp.Variable.PRECIP,
    }


@pytest.mark.anyio
async def test_station_values(fields):
    values = await station_values(fields, STATION_LATS, STATION_LONS)

    assert set(values) == set(ModelRunPrediction.get_weather_model_fields())
    # kelvin to celsius
    assert values[ModelRunPrediction.tmp_tgl_2.name] == pytest.approx([0.0, 10.0], abs=1e-2)
    # from temperature and dewpoint: saturated, then a 10 degree dewpoint depression
    assert values[ModelRunPrediction.rh_tgl_2.name] == pytest.approx([100.0, 49.83], abs=1e-1)
    # metres to mm
    assert values[ModelRunPrediction.apcp_sfc_0.name] == pytest.approx([200.0, 0.0], abs=1e-1)
    # u and v in metres per second to speed in kilometres per hour
    assert values[ModelRunPrediction.wind_tgl_10.name] == pytest.approx([20.99, 36.0], abs=1e-1)
    # u and v to the direction the wind blows from: the second is blowing due south
    wind_direction = values[ModelRunPrediction.wdir_tgl_10.name]
    assert wind_direction[0] == pytest.approx(239.04, abs=1e-1)
    assert min(wind_direction[1], 360 - wind_direction[1]) == pytest.approx(0.0, abs=1e-1)


@pytest.mark.anyio
async def test_station_values_do_not_depend_on_the_order_of_the_fields(fields):
    expected = await station_values(fields, STATION_LATS, STATION_LONS)

    values = await station_values(fields[::-1], STATION_LATS, STATION_LONS)

    for name in expected:
        assert values[name] == pytest.approx(expected[name])
