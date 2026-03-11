import numpy as np
import pytest
from wps_shared.schemas.sfms import SFMSDailyActual

from wps_sfms.interpolation.field import (
    build_attribute_field,
    build_dewpoint_field,
    build_temperature_field,
    build_wind_vector_field,
)


class TestScalarFieldBuilders:
    def test_build_attribute_field_filters_missing_values(self):
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, precipitation=1.5),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, precipitation=None),
        ]

        field = build_attribute_field(actuals, "precipitation")

        np.testing.assert_allclose(field.lats, np.array([49.0], dtype=np.float32))
        np.testing.assert_allclose(field.lons, np.array([-123.0], dtype=np.float32))
        np.testing.assert_allclose(field.values, np.array([1.5], dtype=np.float32))

    def test_build_temperature_field_applies_sea_level_adjustment(self):
        actuals = [
            SFMSDailyActual(
                code=1, lat=49.0, lon=-123.0, elevation=100.0, temperature=15.0
            )
        ]

        field = build_temperature_field(actuals)

        np.testing.assert_allclose(field.values, np.array([15.65], dtype=np.float32), atol=1e-4)

    def test_build_dewpoint_field_skips_missing_elevation_or_value(self):
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, elevation=None, dewpoint=10.0),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, elevation=100.0, dewpoint=None),
        ]

        field = build_dewpoint_field(actuals)

        assert field.lats.size == 0
        assert field.lons.size == 0
        assert field.values.size == 0


class TestWindVectorFieldBuilder:
    def test_build_wind_vector_field_filters_unpaired_values(self):
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, wind_speed=10.0, wind_direction=90.0),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, wind_speed=8.0, wind_direction=None),
        ]

        field = build_wind_vector_field(actuals)

        np.testing.assert_allclose(field.lats, np.array([49.0], dtype=np.float32))
        np.testing.assert_allclose(field.lons, np.array([-123.0], dtype=np.float32))
        np.testing.assert_allclose(field.u, np.array([-10.0], dtype=np.float32), atol=1e-5)
        np.testing.assert_allclose(field.v, np.array([0.0], dtype=np.float32), atol=1e-5)

    def test_build_attribute_field_rejects_unknown_attribute(self):
        with pytest.raises(ValueError, match="Unknown attribute"):
            build_attribute_field([], "not_a_real_field")
