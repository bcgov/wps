from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from wps_weather.wx_4panel_charts.raster_addresser import ECCCModel, RasterAddresser


class ConfigBuilder:
    def __init__(
        self,
        init_ymd: str,
        init_hh: str,
        raster_addresser: RasterAddresser,
        cfg500: Dict[str, Any],
        cfgmslp: Dict[str, Any],
        cfg700: Dict[str, Any],
        cfgpcpn: Dict[str, Any],
        file_name_builder: Callable[[str, str, str, str, str], str],
        model: ECCCModel,
    ):
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
        self.model = model

    def _valid_time_str(self, init_ymd: str, init_hh: str, fh: int) -> str:
        init_dt = datetime.strptime(f"{init_ymd}{init_hh}", "%Y%m%d%H")
        valid_dt = init_dt + timedelta(hours=int(fh))
        return f"F{fh:03d} Valid: {valid_dt:%a %Y-%m-%d %HZ}"

    def build_config_for_hour(self, fh: int):
        """
        Build cfg dicts using weather model grib2 S3 storage structure:
        eg: {bucket}/weather_models/20260217/model_rdps}/10km/{HH}/{FFF}/*.grib2
        """
        # ---- 500 hPa ----
        cfg500 = self.cfg500.copy()
        cfg500["z500_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(
                self.init_ymd, self.init_hh, "GeopotentialHeight", "IsbL-0500", fh
            ),
        )
        cfg500["vort_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(
                self.init_ymd, self.init_hh, "AbsoluteVorticity", "IsbL-0500", fh
            ),
        )
        cfg500["valid_time_str"] = self._valid_time_str(self.init_ymd, self.init_hh, fh)

        # ---- MSLP + thickness ----
        cfgmslp = self.cfgmslp.copy()
        cfgmslp["mslp_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(self.init_ymd, self.init_hh, "Pressure_MSL", None, fh),
        )
        cfgmslp["thk_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(self.init_ymd, self.init_hh, "Thickness", "IsbL-1000to0500", fh),
        )

        # ---- 700 hPa + RH layer mean ----
        cfg700 = self.cfg700.copy()
        cfg700["z700_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(
                self.init_ymd, self.init_hh, "GeopotentialHeight", "IsbL-0700", fh
            ),
        )
        cfg700["rh500_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(
                self.init_ymd, self.init_hh, "RelativeHumidity", "IsbL-0500", fh
            ),
        )
        cfg700["rh700_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(
                self.init_ymd, self.init_hh, "RelativeHumidity", "IsbL-0700", fh
            ),
        )
        cfg700["rh850_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(
                self.init_ymd, self.init_hh, "RelativeHumidity", "IsbL-0850", fh
            ),
        )

        # ---- 3h precip + jet ----
        cfgpcpn = self.cfgpcpn.copy()
        cfgpcpn["jet_spd_grib"] = self.raster_addresser.get_grib_key(
            fh,
            self.file_name_builder(self.init_ymd, self.init_hh, "WindSpeed", "IsbL-0250", fh),
        )

        if fh == 0:
            cfgpcpn["show_precip"] = False  # jet-only at analysis time
        else:
            precip_string = "Precip-Accum12h" if self.model == ECCCModel.GDPS else "Precip-Accum3h"
            cfgpcpn["show_precip"] = True
            cfgpcpn["pcpn_grib"] = self.raster_addresser.get_grib_key(
                fh,
                self.file_name_builder(self.init_ymd, self.init_hh, precip_string, "Sfc", fh),
            )

        return cfg500, cfgmslp, cfg700, cfgpcpn
