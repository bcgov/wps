import enum


class ECCCModel(str, enum.Enum):
    """Enumerator for different kinds of supported ECCC weather models"""

    GDPS = "GDPS"
    RDPS = "RDPS"
    GDPS_GEM = "GDPS_GEM"

WEATHER_MODEL_PREFIX = "weather_models"
FOUR_PANEL_PREFIX = "wx_4panel_charts"
MODEL_GDPS = "model_gdps"
MODEL_RDPS = "model_rdps"
MODEL_GEM_GLOBAL = "model_gem_global"


class WX4PanelChartAddresser:
    def __init__(self, init_ymd: str, init_hh: str, model: ECCCModel):
        self._init_ymd = init_ymd
        self._init_hh = init_hh
        sub_path = None
        if model == ECCCModel.GDPS:
            grid_size = "15km"
            model_path = MODEL_GDPS
        elif model == ECCCModel.RDPS:
            grid_size = "10km"
            model_path = MODEL_RDPS
        elif model == ECCCModel.GDPS_GEM:
            grid_size = "15km"
            model_path = MODEL_GEM_GLOBAL
            sub_path = "/grib2/lat_lon"
        else:
            raise ValueError(f"Unsupported model: {model}")
        self._grid_size = grid_size
        self._model_path = model_path
        self._sub_path = sub_path

    def get_4panel_key(self, fh: str, fname: str):
        prefix = f"{FOUR_PANEL_PREFIX}/{self._init_ymd}/{self._model_path}/{self._grid_size}"
        if self._sub_path is not None:
            prefix += self._sub_path
        key = f"{prefix}/{self._init_hh}/{fh:03d}/{fname}"
        return key

    def get_grib_key(self, fh: int, fname: str):
        prefix = f"{WEATHER_MODEL_PREFIX}/{self._init_ymd}/{self._model_path}/{self._grid_size}"
        if self._sub_path is not None:
            prefix += self._sub_path
        key = f"{prefix}/{self._init_hh}/{fh:03d}/{fname}"
        return key
