from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel, WX4PanelChartAddresser

_GDPS_VARS = {
    "z500": ("GeopotentialHeight", "IsbL-0500"),
    "vort": ("AbsoluteVorticity", "IsbL-0500"),
    "mslp": ("Pressure_MSL", None),
    "thk": ("Thickness", "IsbL-1000to0500"),
    "z700": ("GeopotentialHeight", "IsbL-0700"),
    "rh500": ("RelativeHumidity", "IsbL-0500"),
    "rh700": ("RelativeHumidity", "IsbL-0700"),
    "rh850": ("RelativeHumidity", "IsbL-0850"),
    "precip": ("Precip-Accum6h", "Sfc"),
    "jet_spd": ("WindSpeed", "IsbL-0250"),
}

_VAR_MAP = {
    ECCCModel.GDPS: _GDPS_VARS,
    ECCCModel.RDPS: {**_GDPS_VARS, "precip": ("Precip-Accum3h", "Sfc")},
    ECCCModel.GDPS_GEM: {
        "z500": ("HGT", "ISBL_500"),
        "vort": ("RELV", "ISBL_500"),
        "mslp": ("PRMSL", "MSL_0"),
        "thk": ("HGT", "ISBY_1000-500"),
        "z700": ("HGT", "ISBL_700"),
        "rh500": ("RH", "ISBL_500"),
        "rh700": ("RH", "ISBL_700"),
        "rh850": ("RH", "ISBL_850"),
        "precip": ("APCP-Accum6h", "SFC_0"),
        "jet_spd": ("WIND", "ISBL_250"),
    },
}


class ConfigBuilder:
    def __init__(
        self,
        init_ymd: str,
        init_hh: str,
        raster_addresser: WX4PanelChartAddresser,
        cfg500: Dict[str, Any],
        cfgmslp: Dict[str, Any],
        cfg700: Dict[str, Any],
        cfgpcpn: Dict[str, Any],
        file_name_builder: Callable[[str, str, str, str, str], str],
        model: ECCCModel,
    ):
        """
        Initialize a ConfigBuilder that provides the configuration required to generate 4Panel Charts.

        :param init_ymd: The date for which to generate a chart formatted as YYYYMMdd.
        :param init_hh: The model run hour, either 00 or 12.
        :param raster_addresser: A utility object to provide keys for reading and writing rasters from S3 storage.
        :param cfg500: Configuration for the 500hPa Height and Abs Vorticity panel.
        :param cfgmslp: Configuration for the MSLP and 1000-500 Thickness panel.
        :param cfg700: Configuration for the 700 hPa Height and 850-500 Relative Humidity panel.
        :param cfgpcpn: Configuration for the Precipitation panel.
        :param file_name_builder: A helper function to generate file names of grib2 files used as input.
        :param model: The numerical weather model.
        :raises ValueError: Raises a ValueError if the numerical weather model is not recognized.
        """
        if model not in _VAR_MAP:
            raise ValueError(f"Model must be one of {list(_VAR_MAP)}, received {model}")
        self.model = model
        self._vars = _VAR_MAP[model]
        self.init_ymd = init_ymd
        self.init_hh = init_hh
        self.raster_addresser = raster_addresser
        self.cfg500 = cfg500
        self.cfgmslp = cfgmslp
        self.cfg700 = cfg700
        self.cfgpcpn = cfgpcpn
        self.file_name_builder = file_name_builder

    def _grib_key(self, fh: int, var: str, level: Optional[str]) -> str:
        return self.raster_addresser.get_grib_key(
            fh, self.file_name_builder(self.init_ymd, self.init_hh, var, level, fh)
        )

    def _valid_time_str(self, fh: int) -> str:
        init_dt = datetime.strptime(f"{self.init_ymd}{self.init_hh}", "%Y%m%d%H").replace(
            tzinfo=timezone.utc
        )
        valid_dt = init_dt + timedelta(hours=fh)
        return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"

    def build_config_for_hour(self, fh: int) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Build cfg dicts using weather model grib2 S3 storage structure:
        eg: {bucket}/weather_models/20260217/model_rdps}/10km/{HH}/{FFF}/*.grib2
        """
        model_vars = self._vars

        # ---- 500 hPa ----
        cfg500 = self.cfg500.copy()
        cfg500["z500_grib"] = self._grib_key(fh, *model_vars["z500"])
        cfg500["vort_grib"] = self._grib_key(fh, *model_vars["vort"])
        cfg500["valid_time_str"] = self._valid_time_str(fh)

        # ---- MSLP + thickness ----
        cfgmslp = self.cfgmslp.copy()
        cfgmslp["mslp_grib"] = self._grib_key(fh, *model_vars["mslp"])
        cfgmslp["thk_grib"] = self._grib_key(fh, *model_vars["thk"])

        # ---- 700 hPa + RH layer mean ----
        cfg700 = self.cfg700.copy()
        cfg700["z700_grib"] = self._grib_key(fh, *model_vars["z700"])
        cfg700["rh500_grib"] = self._grib_key(fh, *model_vars["rh500"])
        cfg700["rh700_grib"] = self._grib_key(fh, *model_vars["rh700"])
        cfg700["rh850_grib"] = self._grib_key(fh, *model_vars["rh850"])

        # ---- precip + jet ----
        cfgpcpn = self.cfgpcpn.copy()
        cfgpcpn["jet_spd_grib"] = self._grib_key(fh, *model_vars["jet_spd"])

        if fh == 0:
            cfgpcpn["show_precip"] = False
        else:
            cfgpcpn["show_precip"] = True
            cfgpcpn["pcpn_grib"] = self._grib_key(fh, *model_vars["precip"])

        return cfg500, cfgmslp, cfg700, cfgpcpn
