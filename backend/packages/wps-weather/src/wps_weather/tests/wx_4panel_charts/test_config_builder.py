"""Unit tests for config_builder.py"""
import pytest


@pytest.fixture
def mock_raster_addresser():
    """Create a mock RasterAddresser that returns predictable keys."""
    class MockRasterAddresser:
        def __init__(self):
            self._init_ymd = "20260217"
            self._init_hh = "00"
            self._grid_size = "15km"
            self._model_path = "model_gdps"

        def get_grib_key(self, fh, fname):
            return f"weather_models/20260217/{self._model_path}/{self._grid_size}/00/{fh:03d}/{fname}"

    return MockRasterAddresser()


def simple_file_name_builder(init_ymd, init_hh, parameter, isbl, fh):
    """Simple file name builder for testing."""
    parts = [init_ymd, init_hh, parameter]
    if isbl:
        parts.append(isbl)
    parts.append(f"f{fh}")
    return "_".join(parts) + ".grib2"


class TestConfigBuilderConstructor:
    """Tests for ConfigBuilder constructor validation."""

    def test_valid_model_gdps(self, fake_wps_modules, mock_raster_addresser):
        """Test that GDPS model is accepted."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )
        assert builder.model == ECCCModel.GDPS

    def test_valid_model_rdps(self, fake_wps_modules, mock_raster_addresser):
        """Test that RDPS model is accepted."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        mock_raster_addresser._model_path = "model_rdps"
        mock_raster_addresser._grid_size = "10km"

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.RDPS,
        )
        assert builder.model == ECCCModel.RDPS

    def test_invalid_model_raises_value_error(self, fake_wps_modules, mock_raster_addresser):
        """Test that invalid model raises ValueError."""
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        class FakeModel:
            pass

        with pytest.raises(ValueError) as exc:
            ConfigBuilder(
                init_ymd="20260217",
                init_hh="00",
                raster_addresser=mock_raster_addresser,
                cfg500={"z500_grib": ""},
                cfgmslp={"mslp_grib": ""},
                cfg700={"z700_grib": ""},
                cfgpcpn={"jet_spd_grib": ""},
                file_name_builder=simple_file_name_builder,
                model=FakeModel(),
            )
        assert "Model must be one of GDPS or RDPS" in str(exc.value)


class TestValidTimeStr:
    """Tests for _valid_time_str method."""

    def test_valid_time_str_basic(self, fake_wps_modules, mock_raster_addresser):
        """Test _valid_time_str returns expected format."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )
        result = builder._valid_time_str("20260217", "00", 0)
        assert "F000" in result
        assert "Valid:" in result

    def test_valid_time_str_with_forecast_hour(self, fake_wps_modules, mock_raster_addresser):
        """Test _valid_time_str with different forecast hours."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )
        result = builder._valid_time_str("20260217", "00", 6)
        assert "F006" in result

    def test_valid_time_str_adds_hours_correctly(self, fake_wps_modules, mock_raster_addresser):
        """Test that _valid_time_str correctly adds hours to init time."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )
        # 2026-02-17 00:00 + 6 hours = 2026-02-17 06:00
        result = builder._valid_time_str("20260217", "00", 6)
        assert "2026-02-17" in result
        assert "06Z" in result

    def test_valid_time_str_day_rollover(self, fake_wps_modules, mock_raster_addresser):
        """Test _valid_time_str handles day rollover correctly."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )
        # 2026-02-17 00:00 + 24 hours = 2026-02-18 00:00
        result = builder._valid_time_str("20260217", "00", 24)
        assert "2026-02-18" in result
        assert "00Z" in result


class TestBuildConfigForHour:
    """Tests for build_config_for_hour method."""

    def test_build_config_returns_tuple_of_dicts(self, fake_wps_modules, mock_raster_addresser):
        """Test build_config_for_hour returns a tuple of 4 dicts."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        result = builder.build_config_for_hour(fh=6)
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_build_config_500hpa_has_required_keys(self, fake_wps_modules, mock_raster_addresser):
        """Test 500hPa config has required keys."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=6)

        assert "z500_grib" in cfg500
        assert "vort_grib" in cfg500
        assert "valid_time_str" in cfg500
        # Verify keys are not empty
        assert cfg500["z500_grib"]
        assert cfg500["vort_grib"]

    def test_build_config_mslp_has_required_keys(self, fake_wps_modules, mock_raster_addresser):
        """Test MSLP config has required keys."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=6)

        assert "mslp_grib" in cfgmslp
        assert "thk_grib" in cfgmslp
        assert cfgmslp["mslp_grib"]
        assert cfgmslp["thk_grib"]

    def test_build_config_700hpa_has_required_keys(self, fake_wps_modules, mock_raster_addresser):
        """Test 700hPa config has required keys."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=6)

        assert "z700_grib" in cfg700
        assert "rh500_grib" in cfg700
        assert "rh700_grib" in cfg700
        assert "rh850_grib" in cfg700

    def test_build_config_pcpn_has_jet_speed(self, fake_wps_modules, mock_raster_addresser):
        """Test precipitation config has jet speed."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=6)

        assert "jet_spd_grib" in cfgpcpn
        assert cfgpcpn["jet_spd_grib"]

    def test_build_config_fh_zero_no_precip(self, fake_wps_modules, mock_raster_addresser):
        """Test fh=0 shows no precipitation."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=0)

        assert cfgpcpn["show_precip"] is False

    def test_build_config_gdps_uses_12h_precip(self, fake_wps_modules, mock_raster_addresser):
        """Test GDPS model uses 12h precipitation."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=12)

        assert cfgpcpn["show_precip"] is True
        assert "pcpn_grib" in cfgpcpn
        # The file name should contain Precip-Accum12h for GDPS
        assert "Precip-Accum12h" in cfgpcpn["pcpn_grib"]

    def test_build_config_rdps_uses_3h_precip(self, fake_wps_modules):
        """Test RDPS model uses 3h precipitation."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        class MockRasterAddresserRDPS:
            def __init__(self):
                self._init_ymd = "20260217"
                self._init_hh = "00"
                self._grid_size = "10km"
                self._model_path = "model_rdps"

            def get_grib_key(self, fh, fname):
                return f"weather_models/20260217/{self._model_path}/{self._grid_size}/00/{fh:03d}/{fname}"

        mock_raster = MockRasterAddresserRDPS()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.RDPS,
        )

        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(fh=3)

        assert cfgpcpn["show_precip"] is True
        assert "pcpn_grib" in cfgpcpn
        # The file name should contain Precip-Accum3h for RDPS
        assert "Precip-Accum3h" in cfgpcpn["pcpn_grib"]

    def test_build_config_different_fh_same_structure(self, fake_wps_modules, mock_raster_addresser):
        """Test different forecast hours produce configs with same structure."""
        ECCCModel = fake_wps_modules.get_ECCCModel()
        ConfigBuilder = fake_wps_modules.get_config_builder_class()

        builder = ConfigBuilder(
            init_ymd="20260217",
            init_hh="00",
            raster_addresser=mock_raster_addresser,
            cfg500={"z500_grib": "", "vort_grib": "", "valid_time_str": ""},
            cfgmslp={"mslp_grib": "", "thk_grib": ""},
            cfg700={"z700_grib": "", "rh500_grib": "", "rh700_grib": "", "rh850_grib": ""},
            cfgpcpn={"jet_spd_grib": "", "show_precip": False, "pcpn_grib": ""},
            file_name_builder=simple_file_name_builder,
            model=ECCCModel.GDPS,
        )

        result_fh6 = builder.build_config_for_hour(fh=6)
        result_fh12 = builder.build_config_for_hour(fh=12)

        cfg500_6, cfgmslp_6, cfg700_6, cfgpcpn_6 = result_fh6
        cfg500_12, cfgmslp_12, cfg700_12, cfgpcpn_12 = result_fh12

        # Both should have same keys
        assert set(cfg500_6.keys()) == set(cfg500_12.keys())
        assert set(cfgmslp_6.keys()) == set(cfgmslp_12.keys())
        assert set(cfg700_6.keys()) == set(cfg700_12.keys())
        assert set(cfgpcpn_6.keys()) == set(cfgpcpn_12.keys())
