import pytest
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import StationActualSource


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
