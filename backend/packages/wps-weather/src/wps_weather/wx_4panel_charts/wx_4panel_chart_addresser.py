import enum


class ECCCModel(str, enum.Enum):
    """Enumerator for different kinds of supported ECCC weather models"""

    GDPS = "GDPS"
    RDPS = "RDPS"

WEATHER_MODEL_PREFIX = "weather_models"
FOUR_PANEL_PREFIX = "wx_4panel_charts"
MODEL_GDPS = "model_gdps"
MODEL_RDPS = "model_rdps"


class WX4PanelChartAddresser:
    def __init__(self, init_ymd: str, init_hh: str, model: ECCCModel):
        self._init_ymd = init_ymd
        self._init_hh = init_hh
        if model == ECCCModel.GDPS:
            grid_size = "15km"
            model_path = MODEL_GDPS
        elif model == ECCCModel.RDPS:
            grid_size = "10km"
            model_path = MODEL_RDPS
        self._grid_size = grid_size
        self._model_path = model_path

    def get_4panel_key(self, fh: int, fname: str):
        """The lowercase key a 4-panel chart is stored under. Charts use lowercase keys for GeoDrive."""
        key = f"{FOUR_PANEL_PREFIX}/{self._init_ymd}/{self._model_path}/{self._grid_size}/{self._init_hh}/{fh:03d}/{fname}"
        return key.lower()

    def get_grib_key(self, fh: int, fname: str):
        """The lowercase key a GRIB is read from. GRIBs are stored under lowercase keys for GeoDrive."""
        key = f"{WEATHER_MODEL_PREFIX}/{self._init_ymd}/{self._model_path}/{self._grid_size}/{self._init_hh}/{fh:03d}/{fname}"
        return key.lower()
