from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel


@pytest.fixture()
def mock_raster_addresser():
    """Return a mock RasterAddresser whose get_grib_key returns a predictable string."""
    addresser = MagicMock()
    addresser.get_grib_key.side_effect = lambda fh, key: f"s3://bucket/{key}"
    return addresser


@pytest.fixture()
def mock_file_name_builder():
    """Return a mock file_name_builder that produces a readable, deterministic key."""
    return MagicMock(
        side_effect=lambda ymd, hh, var, level, fh: f"{ymd}_{hh}_{var}_{level}_{fh:03d}"
    )


@pytest.fixture()
def base_cfg():
    return {
        "cfg500": {"extent": [-140, 40, -50, 80]},
        "cfgmslp": {"cmap": "RdBu"},
        "cfg700": {"alpha": 0.8},
        "cfgpcpn": {"threshold": 1.0},
    }


def make_builder(model, mock_raster_addresser, mock_file_name_builder, base_cfg):
    from wps_weather.wx_4panel_charts.config_builder import ConfigBuilder

    return ConfigBuilder(
        init_ymd="20260217",
        init_hh="00",
        raster_addresser=mock_raster_addresser,
        cfg500=base_cfg["cfg500"],
        cfgmslp=base_cfg["cfgmslp"],
        cfg700=base_cfg["cfg700"],
        cfgpcpn=base_cfg["cfgpcpn"],
        file_name_builder=mock_file_name_builder,
        model=model,
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestConfigBuilderInit:
    @pytest.mark.parametrize(
        "model, expected_model",
        [
            ("GDPS", ECCCModel.GDPS),
            ("RDPS", ECCCModel.RDPS),
        ],
    )
    def test_initialises_successfully(
        self, model, expected_model, mock_raster_addresser, mock_file_name_builder, base_cfg
    ):
        builder = make_builder(model, mock_raster_addresser, mock_file_name_builder, base_cfg)
        assert builder.model == expected_model

    def test_unsupported_model_raises_value_error(
        self, mock_raster_addresser, mock_file_name_builder, base_cfg
    ):
        from wps_weather.wx_4panel_charts.config_builder import ConfigBuilder

        with pytest.raises(ValueError, match="Model must be one of GDPS or RDPS"):
            ConfigBuilder(
                init_ymd="20260217",
                init_hh="00",
                raster_addresser=mock_raster_addresser,
                cfg500=base_cfg["cfg500"],
                cfgmslp=base_cfg["cfgmslp"],
                cfg700=base_cfg["cfg700"],
                cfgpcpn=base_cfg["cfgpcpn"],
                file_name_builder=mock_file_name_builder,
                model="UNSUPPORTED",
            )

    def test_init_stores_all_attributes(
        self, mock_raster_addresser, mock_file_name_builder, base_cfg
    ):
        builder = make_builder(
            ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg
        )
        assert builder.init_ymd == "20260217"
        assert builder.init_hh == "00"
        assert builder.raster_addresser is mock_raster_addresser
        assert builder.file_name_builder is mock_file_name_builder


# ---------------------------------------------------------------------------
# _valid_time_str
# ---------------------------------------------------------------------------


class TestValidTimeStr:
    @pytest.fixture()
    def builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    def test_fh_zero_equals_init_time(self, builder):
        result = builder._valid_time_str(0)
        assert result == "F000 Valid: Tue 2026-02-17 00Z"

    def test_fh_advances_by_correct_hours(self, builder):
        result = builder._valid_time_str(24)
        assert result == "F024 Valid: Wed 2026-02-18 00Z"

    def test_fh_crosses_midnight(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        # Use init_hh="12" so fh=12 crosses into the next day
        from wps_weather.wx_4panel_charts.config_builder import ConfigBuilder
        from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel

        b = ConfigBuilder(
            init_ymd="20260217",
            init_hh="12",
            raster_addresser=mock_raster_addresser,
            cfg500=base_cfg["cfg500"],
            cfgmslp=base_cfg["cfgmslp"],
            cfg700=base_cfg["cfg700"],
            cfgpcpn=base_cfg["cfgpcpn"],
            file_name_builder=mock_file_name_builder,
            model=ECCCModel.GDPS,
        )
        result = b._valid_time_str(12)
        assert result == "F012 Valid: Wed 2026-02-18 00Z"

    def test_fh_format_zero_pads_to_three_digits(self, builder):
        result = builder._valid_time_str(6)
        assert result.startswith("F006 ")

    def test_fh_large_value_zero_pads_correctly(self, builder):
        result = builder._valid_time_str(240)
        assert result.startswith("F240 ")

    def test_valid_time_str_contains_valid_prefix(self, builder):
        result = builder._valid_time_str(12)
        assert "Valid:" in result


# ---------------------------------------------------------------------------
# build_config_for_hour — 500 hPa block
# ---------------------------------------------------------------------------


class TestBuildConfigForHour500hPa:
    @pytest.fixture()
    def builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    def test_z500_grib_key_is_set(self, builder):
        cfg500, *_ = builder.build_config_for_hour(12)
        assert "z500_grib" in cfg500

    def test_vort_grib_key_is_set(self, builder):
        cfg500, *_ = builder.build_config_for_hour(12)
        assert "vort_grib" in cfg500

    def test_valid_time_str_is_set(self, builder):
        cfg500, *_ = builder.build_config_for_hour(12)
        assert "valid_time_str" in cfg500

    def test_z500_grib_uses_geopotential_height_variable(self, builder, mock_file_name_builder):
        builder.build_config_for_hour(12)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("GeopotentialHeight" in c and "IsbL-0500" in c for c in calls)

    def test_vort_grib_uses_absolute_vorticity_variable(self, builder, mock_file_name_builder):
        builder.build_config_for_hour(12)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("AbsoluteVorticity" in c and "IsbL-0500" in c for c in calls)

    def test_original_cfg500_is_not_mutated(self, builder, base_cfg):
        original = base_cfg["cfg500"].copy()
        builder.build_config_for_hour(12)
        assert base_cfg["cfg500"] == original


# ---------------------------------------------------------------------------
# build_config_for_hour — MSLP block
# ---------------------------------------------------------------------------


class TestBuildConfigForHourMslp:
    @pytest.fixture()
    def builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    def test_mslp_grib_key_is_set(self, builder):
        _, cfgmslp, *_ = builder.build_config_for_hour(12)
        assert "mslp_grib" in cfgmslp

    def test_thk_grib_key_is_set(self, builder):
        _, cfgmslp, *_ = builder.build_config_for_hour(12)
        assert "thk_grib" in cfgmslp

    def test_mslp_grib_uses_pressure_msl_variable(self, builder, mock_file_name_builder):
        builder.build_config_for_hour(12)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("Pressure_MSL" in c for c in calls)

    def test_thickness_grib_uses_correct_layer(self, builder, mock_file_name_builder):
        builder.build_config_for_hour(12)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("Thickness" in c and "IsbL-1000to0500" in c for c in calls)

    def test_original_cfgmslp_is_not_mutated(self, builder, base_cfg):
        original = base_cfg["cfgmslp"].copy()
        builder.build_config_for_hour(12)
        assert base_cfg["cfgmslp"] == original


# ---------------------------------------------------------------------------
# build_config_for_hour — 700 hPa block
# ---------------------------------------------------------------------------


class TestBuildConfigForHour700hPa:
    @pytest.fixture()
    def builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    def test_z700_grib_key_is_set(self, builder):
        *_, cfg700, _ = builder.build_config_for_hour(12)
        assert "z700_grib" in cfg700

    def test_rh500_grib_key_is_set(self, builder):
        *_, cfg700, _ = builder.build_config_for_hour(12)
        assert "rh500_grib" in cfg700

    def test_rh700_grib_key_is_set(self, builder):
        *_, cfg700, _ = builder.build_config_for_hour(12)
        assert "rh700_grib" in cfg700

    def test_rh850_grib_key_is_set(self, builder):
        *_, cfg700, _ = builder.build_config_for_hour(12)
        assert "rh850_grib" in cfg700

    def test_all_three_rh_levels_requested(self, builder, mock_file_name_builder):
        builder.build_config_for_hour(12)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        rh_calls = [c for c in calls if "RelativeHumidity" in c]
        levels = {"IsbL-0500", "IsbL-0700", "IsbL-0850"}
        assert all(any(lvl in c for c in rh_calls) for lvl in levels)

    def test_original_cfg700_is_not_mutated(self, builder, base_cfg):
        original = base_cfg["cfg700"].copy()
        builder.build_config_for_hour(12)
        assert base_cfg["cfg700"] == original


# ---------------------------------------------------------------------------
# build_config_for_hour — precipitation block
# ---------------------------------------------------------------------------


class TestBuildConfigForHourPcpn:
    @pytest.fixture()
    def gdps_builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    @pytest.fixture()
    def rdps_builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.RDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    def test_jet_spd_grib_key_always_set(self, gdps_builder):
        *_, cfgpcpn = gdps_builder.build_config_for_hour(12)
        assert "jet_spd_grib" in cfgpcpn

    def test_jet_spd_grib_uses_wind_speed_at_250hpa(self, gdps_builder, mock_file_name_builder):
        gdps_builder.build_config_for_hour(12)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("WindSpeed" in c and "IsbL-0250" in c for c in calls)

    # fh == 0 (analysis time)
    def test_fh0_show_precip_is_false(self, gdps_builder):
        *_, cfgpcpn = gdps_builder.build_config_for_hour(0)
        assert cfgpcpn["show_precip"] is False

    def test_fh0_pcpn_grib_not_set(self, gdps_builder):
        *_, cfgpcpn = gdps_builder.build_config_for_hour(0)
        assert "pcpn_grib" not in cfgpcpn

    # fh > 0 — precip enabled
    def test_fh_nonzero_show_precip_is_true(self, gdps_builder):
        *_, cfgpcpn = gdps_builder.build_config_for_hour(12)
        assert cfgpcpn["show_precip"] is True

    def test_fh_nonzero_pcpn_grib_is_set(self, gdps_builder):
        *_, cfgpcpn = gdps_builder.build_config_for_hour(12)
        assert "pcpn_grib" in cfgpcpn

    # GDPS uses 6h accumulation
    def test_gdps_uses_6h_precip_accumulation(self, gdps_builder, mock_file_name_builder):
        gdps_builder.build_config_for_hour(6)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("Precip-Accum6h" in c for c in calls)

    def test_gdps_does_not_use_3h_precip_accumulation(self, gdps_builder, mock_file_name_builder):
        gdps_builder.build_config_for_hour(6)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert not any("Precip-Accum3h" in c for c in calls)

    # RDPS uses 3h accumulation
    def test_rdps_uses_3h_precip_accumulation(self, rdps_builder, mock_file_name_builder):
        rdps_builder.build_config_for_hour(6)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("Precip-Accum3h" in c for c in calls)

    def test_rdps_does_not_use_6h_precip_accumulation(self, rdps_builder, mock_file_name_builder):
        rdps_builder.build_config_for_hour(6)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert not any("Precip-Accum12h" in c for c in calls)

    def test_precip_grib_uses_sfc_level(self, gdps_builder, mock_file_name_builder):
        gdps_builder.build_config_for_hour(6)
        calls = [str(c) for c in mock_file_name_builder.call_args_list]
        assert any("Precip-Accum6h" in c and "Sfc" in c for c in calls)

    def test_original_cfgpcpn_is_not_mutated(self, gdps_builder, base_cfg):
        original = base_cfg["cfgpcpn"].copy()
        gdps_builder.build_config_for_hour(12)
        assert base_cfg["cfgpcpn"] == original


# ---------------------------------------------------------------------------
# Return value shape
# ---------------------------------------------------------------------------

class TestBuildConfigForHourReturnShape:
    @pytest.fixture()
    def builder(self, mock_raster_addresser, mock_file_name_builder, base_cfg):
        return make_builder(ECCCModel.GDPS, mock_raster_addresser, mock_file_name_builder, base_cfg)

    def test_returns_four_dicts(self, builder):
        result = builder.build_config_for_hour(12)
        assert len(result) == 4
        assert all(isinstance(r, dict) for r in result)

    def test_returned_dicts_are_copies_not_originals(self, builder, base_cfg):
        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(12)
        assert cfg500 is not base_cfg["cfg500"]
        assert cfgmslp is not base_cfg["cfgmslp"]
        assert cfg700 is not base_cfg["cfg700"]
        assert cfgpcpn is not base_cfg["cfgpcpn"]

    def test_original_keys_preserved_in_returned_dicts(self, builder, base_cfg):
        cfg500, cfgmslp, cfg700, cfgpcpn = builder.build_config_for_hour(12)
        assert cfg500["extent"] == base_cfg["cfg500"]["extent"]
        assert cfgmslp["cmap"] == base_cfg["cfgmslp"]["cmap"]
        assert cfg700["alpha"] == base_cfg["cfg700"]["alpha"]
        assert cfgpcpn["threshold"] == base_cfg["cfgpcpn"]["threshold"]

    def test_raster_addresser_called_for_each_grib_key(self, builder, mock_raster_addresser):
        builder.build_config_for_hour(12)
        # 500 (z, vort) + mslp (mslp, thk) + 700 (z700, rh500, rh700, rh850) + pcpn (jet, pcpn) = 10
        assert mock_raster_addresser.get_grib_key.call_count == 10

    def test_raster_addresser_called_fewer_times_at_fh0(self, builder, mock_raster_addresser):
        builder.build_config_for_hour(0)
        # pcpn_grib is skipped at fh==0, so 9 calls instead of 10
        assert mock_raster_addresser.get_grib_key.call_count == 9