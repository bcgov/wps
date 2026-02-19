"""Tests for ECMWFGribProcessor."""

import math

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from unittest.mock import patch, MagicMock

from weather_model_jobs.ecmwf_grib_processor import (
    ECMWFGribProcessor,
    TEMP_FIELD,
    DEW_FIELD,
    U_WIND_FIELD,
    V_WIND_FIELD,
    PRECIP_FIELD,
    WIND_SPEED_FIELD,
    WIND_DIR_FIELD,
    RH_FIELD,
)


@pytest.fixture
def processor():
    return ECMWFGribProcessor()


@pytest.fixture
def sample_dataset():
    """Create a minimal xarray Dataset mimicking ECMWF GRIB output."""
    lat = np.array([49.0, 50.0, 51.0])
    lon = np.array([-120.0, -121.0, -122.0])

    temp_data = np.full((3, 3), 293.15)  # 20°C in Kelvin
    dew_data = np.full((3, 3), 283.15)  # 10°C in Kelvin
    u_data = np.full((3, 3), 5.0)  # m/s
    v_data = np.full((3, 3), 5.0)  # m/s
    precip_data = np.full((3, 3), 0.005)  # 5mm in metres

    ds = xr.Dataset(
        {
            TEMP_FIELD: (["latitude", "longitude"], temp_data),
            DEW_FIELD: (["latitude", "longitude"], dew_data),
            U_WIND_FIELD: (["latitude", "longitude"], u_data),
            V_WIND_FIELD: (["latitude", "longitude"], v_data),
            PRECIP_FIELD: (["latitude", "longitude"], precip_data),
        },
        coords={"latitude": lat, "longitude": lon},
    )
    return ds


@pytest.fixture
def stations_df():
    """Create a station DataFrame matching the expected format."""
    return pd.DataFrame(
        {
            "latitude": [49.0, 50.0],
            "longitude": [-120.0, -121.0],
            "code": [100, 200],
        }
    )


class TestComputeWind:
    def test_wind_speed_from_components(self, processor, sample_dataset):
        ds = processor._compute_wind(sample_dataset)
        expected_speed = math.sqrt(5.0**2 + 5.0**2)
        np.testing.assert_allclose(ds[WIND_SPEED_FIELD].values, expected_speed, rtol=1e-6)

    def test_wind_direction_from_components(self, processor):
        lat = np.array([50.0])
        lon = np.array([-120.0])

        # Wind blowing southward (v=-10): comes FROM north = 0°/360°
        ds = xr.Dataset(
            {
                U_WIND_FIELD: (["latitude", "longitude"], [[0.0]]),
                V_WIND_FIELD: (["latitude", "longitude"], [[-10.0]]),
            },
            coords={"latitude": lat, "longitude": lon},
        )
        ds = processor._compute_wind(ds)
        # 0° and 360° are equivalent for north
        np.testing.assert_allclose(ds[WIND_DIR_FIELD].values % 360, 0.0, atol=0.1)

    def test_wind_direction_east(self, processor):
        lat = np.array([50.0])
        lon = np.array([-120.0])

        # Wind blowing westward (u=-10): comes FROM east = 90°
        ds = xr.Dataset(
            {
                U_WIND_FIELD: (["latitude", "longitude"], [[-10.0]]),
                V_WIND_FIELD: (["latitude", "longitude"], [[0.0]]),
            },
            coords={"latitude": lat, "longitude": lon},
        )
        ds = processor._compute_wind(ds)
        np.testing.assert_allclose(ds[WIND_DIR_FIELD].values, 90.0, atol=0.1)

    def test_wind_direction_range(self, processor, sample_dataset):
        ds = processor._compute_wind(sample_dataset)
        assert (ds[WIND_DIR_FIELD].values >= 0).all()
        assert (ds[WIND_DIR_FIELD].values < 360).all()


class TestExtractStationData:
    def test_nearest_neighbor_extraction(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        station_ds = processor._extract_station_data(ds, stations_df)

        assert "point_code" in station_ds.dims
        assert len(station_ds.point_code) == 2
        assert set(station_ds.point_code.values) == {100, 200}

    def test_station_values_match_grid(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        station_ds = processor._extract_station_data(ds, stations_df)

        # Station at (49.0, -120.0) should get the value at grid point (49.0, -120.0)
        np.testing.assert_allclose(
            station_ds[TEMP_FIELD].sel(point_code=100).values,
            293.15,
            rtol=1e-6,
        )


class TestConvertUnits:
    def test_temperature_kelvin_to_celsius(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        ds = processor._extract_station_data(ds, stations_df)
        ds = processor._convert_units(ds)

        # 293.15K = 20°C
        np.testing.assert_allclose(ds[TEMP_FIELD].sel(point_code=100).values, 20.0, atol=0.01)

    def test_wind_speed_mps_to_kph(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        ds = processor._extract_station_data(ds, stations_df)

        # Before conversion: sqrt(25+25) ≈ 7.071 m/s
        original_speed = math.sqrt(50)
        ds = processor._convert_units(ds)

        # After conversion: m/s * 3.6 = km/h
        expected_kph = original_speed / 1000 * 3600
        np.testing.assert_allclose(ds[WIND_SPEED_FIELD].sel(point_code=100).values, expected_kph, rtol=1e-4)

    def test_precip_m_to_mm(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        ds = processor._extract_station_data(ds, stations_df)
        ds = processor._convert_units(ds)

        # 0.005m = 5mm
        np.testing.assert_allclose(ds[PRECIP_FIELD].sel(point_code=100).values, 5.0, atol=0.01)

    def test_rh_calculation(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        ds = processor._extract_station_data(ds, stations_df)
        ds = processor._convert_units(ds)

        # RH should be between 0 and 100 for reasonable temp/dew point
        rh_val = ds[RH_FIELD].sel(point_code=100).values
        assert 0 < rh_val < 100
        # For temp=293.15K (20°C) and dew=283.15K (10°C), RH ≈ 52%
        np.testing.assert_allclose(rh_val, 52.58, atol=1.0)


class TestRenameToDbFields:
    def test_field_renaming(self, processor, sample_dataset, stations_df):
        ds = processor._compute_wind(sample_dataset)
        ds = processor._extract_station_data(ds, stations_df)
        ds = processor._convert_units(ds)
        ds = processor._rename_to_db_fields(ds)

        assert "tmp_tgl_2" in ds.data_vars
        assert "rh_tgl_2" in ds.data_vars
        assert "apcp_sfc_0" in ds.data_vars
        assert "wind_tgl_10" in ds.data_vars
        assert "wdir_tgl_10" in ds.data_vars

    def test_full_process_pipeline(self, processor, stations_df):
        """Test the full process method with a mocked _load_weather_dataset."""
        lat = np.array([49.0, 50.0])
        lon = np.array([-120.0, -121.0])

        ds = xr.Dataset(
            {
                TEMP_FIELD: (["latitude", "longitude"], np.full((2, 2), 300.0)),
                DEW_FIELD: (["latitude", "longitude"], np.full((2, 2), 290.0)),
                U_WIND_FIELD: (["latitude", "longitude"], np.full((2, 2), 3.0)),
                V_WIND_FIELD: (["latitude", "longitude"], np.full((2, 2), 4.0)),
                PRECIP_FIELD: (["latitude", "longitude"], np.full((2, 2), 0.002)),
            },
            coords={"latitude": lat, "longitude": lon},
        )

        with patch.object(processor, "_load_weather_dataset", return_value=ds):
            result = processor.process("fake.grib2", stations_df)

        assert "tmp_tgl_2" in result.data_vars
        assert "rh_tgl_2" in result.data_vars
        assert "apcp_sfc_0" in result.data_vars
        assert "wind_tgl_10" in result.data_vars
        assert "wdir_tgl_10" in result.data_vars
        assert len(result.point_code) == 2
