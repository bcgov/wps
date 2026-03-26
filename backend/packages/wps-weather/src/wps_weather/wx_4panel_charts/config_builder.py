from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple

from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel, WX4PanelChartAddresser


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
        if model not in [ECCCModel.GDPS, ECCCModel.RDPS]:
            raise ValueError(f"Model must be one of GDPS or RDPS, received {model}")
        self.model = model
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
        init_dt = datetime.strptime(f"{self.init_ymd}{self.init_hh}", "%Y%m%d%H")
        valid_dt = init_dt + timedelta(hours=fh)
        return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"

    def build_config_for_hour(self, fh: int) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Build cfg dicts using weather model grib2 S3 storage structure:
        eg: {bucket}/weather_models/20260217/model_rdps}/10km/{HH}/{FFF}/*.grib2
        """
        # ---- 500 hPa ----
        cfg500 = self.cfg500.copy()
        cfg500["z500_grib"] = self._grib_key(fh, "GeopotentialHeight", "IsbL-0500")
        cfg500["vort_grib"] = self._grib_key(fh, "AbsoluteVorticity", "IsbL-0500")
        cfg500["valid_time_str"] = self._valid_time_str(fh)

        # ---- MSLP + thickness ----
        cfgmslp = self.cfgmslp.copy()
        cfgmslp["mslp_grib"] = self._grib_key(fh, "Pressure_MSL", None)
        cfgmslp["thk_grib"] = self._grib_key(fh, "Thickness", "IsbL-1000to0500")

        # ---- 700 hPa + RH layer mean ----
        cfg700 = self.cfg700.copy()
        cfg700["z700_grib"] = self._grib_key(fh, "GeopotentialHeight", "IsbL-0700")
        cfg700["rh500_grib"] = self._grib_key(fh, "RelativeHumidity", "IsbL-0500")
        cfg700["rh700_grib"] = self._grib_key(fh, "RelativeHumidity", "IsbL-0700")
        cfg700["rh850_grib"] = self._grib_key(fh, "RelativeHumidity", "IsbL-0850")

        # ---- 3h precip + jet ----
        cfgpcpn = self.cfgpcpn.copy()
        cfgpcpn["jet_spd_grib"] = self._grib_key(fh, "WindSpeed", "IsbL-0250")

        if fh == 0:
            cfgpcpn["show_precip"] = False  # jet-only at analysis time
        else:
            precip_string = "Precip-Accum12h" if self.model == ECCCModel.GDPS else "Precip-Accum3h"
            cfgpcpn["show_precip"] = True
            cfgpcpn["pcpn_grib"] = self._grib_key(fh, precip_string, "Sfc")


        return cfg500, cfgmslp, cfg700, cfgpcpn
