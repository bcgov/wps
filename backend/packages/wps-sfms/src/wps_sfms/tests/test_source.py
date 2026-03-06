import numpy as np
import pytest
from wps_sfms.processors.wind import WindDirectionInterpolator
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import StationActualSource, StationWindVectorSource


class TestStationActualSource:
    """Tests for StationActualSource attribute validation."""

    def test_valid_attribute_constructs_successfully(self):
        """Test that a valid attribute name constructs without error."""
        actuals = [SFMSDailyActual(code=1, lat=49.0, lon=-123.0, precipitation=5.0)]
        source = StationActualSource("precipitation", actuals)
        lats, _, values = source.get_interpolation_data()
        assert len(lats) == 1
        assert values[0] == pytest.approx(5.0)

    def test_invalid_attribute_raises_value_error(self):
        """Test that an unknown attribute name raises ValueError at construction."""
        actuals = [SFMSDailyActual(code=1, lat=49.0, lon=-123.0)]
        with pytest.raises(ValueError, match="Unknown attribute"):
            StationActualSource("not_a_real_field", actuals)

    def test_none_values_are_excluded(self):
        """Test that stations with None for the target attribute are excluded."""
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, precipitation=3.0),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, precipitation=None),
        ]
        source = StationActualSource("precipitation", actuals)
        lats, _, values = source.get_interpolation_data()
        assert len(lats) == 1
        assert values[0] == pytest.approx(3.0)


class TestStationWindVectorSource:
    """Tests for StationWindVectorSource paired wind vector extraction."""

    def test_get_interpolation_data_filters_unpaired_values(self):
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, wind_speed=10.0, wind_direction=0.0),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, wind_speed=8.0, wind_direction=90.0),
            SFMSDailyActual(code=3, lat=49.2, lon=-123.2, wind_speed=12.0, wind_direction=None),
            SFMSDailyActual(code=4, lat=49.3, lon=-123.3, wind_speed=None, wind_direction=180.0),
        ]
        source = StationWindVectorSource(actuals)

        lats, lons, u, v = source.get_interpolation_data()

        assert len(lats) == 2
        assert len(lons) == 2

        # For dir=0: u=-ws*sin(0)=0, v=-ws*cos(0)=-10
        assert u[0] == pytest.approx(0.0, abs=1e-6)
        assert v[0] == pytest.approx(-10.0)
        # For dir=90: u=-ws*sin(90)=-8, v=-ws*cos(90)=0
        assert u[1] == pytest.approx(-8.0, abs=1e-5)
        assert v[1] == pytest.approx(0.0, abs=1e-5)

    def test_get_interpolation_data_returns_empty_when_no_pairs(self):
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, wind_speed=None, wind_direction=0.0),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, wind_speed=5.0, wind_direction=None),
        ]
        source = StationWindVectorSource(actuals)

        lats, lons, u, v = source.get_interpolation_data()
        assert len(lats) == 0
        assert len(lons) == 0
        assert len(u) == 0
        assert len(v) == 0

    @pytest.mark.parametrize(
        "direction_deg,wind_speed",
        [
            (45.0, 10.0),
            (135.0, 8.0),
            (225.0, 5.0),
            (315.0, 12.0),
            (180.0, 6.0),
        ],
    )
    def test_uv_roundtrip(self, direction_deg, wind_speed):
        """Encoding a direction to u/v then reconstructing it must return the original direction."""
        actuals = [
            SFMSDailyActual(
                code=1, lat=49.0, lon=-123.0, wind_speed=wind_speed, wind_direction=direction_deg
            )
        ]
        source = StationWindVectorSource(actuals)
        _, _, u, v = source.get_interpolation_data()

        reconstructed = WindDirectionInterpolator.compute_direction_from_uv(u, v)

        np.testing.assert_allclose(reconstructed, [direction_deg], atol=0.01)
