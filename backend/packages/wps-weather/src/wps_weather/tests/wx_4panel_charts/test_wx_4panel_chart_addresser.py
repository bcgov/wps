from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel, WX4PanelChartAddresser

INIT_YMD = "20260318"
INIT_HH = "00"
FH = 7
FNAME = "four_panel.png"
GRIB_NAME = "20260318T00Z_MSC_GDPS_Precip-Accum6h_Sfc_LatLon0.15_PT007H.grib2"


def test_get_4panel_key_gdps():
    ra = WX4PanelChartAddresser(init_ymd=INIT_YMD, init_hh=INIT_HH, model=ECCCModel.GDPS)
    result = ra.get_4panel_key(fh=FH, fname=FNAME)
    assert result == f"wx_4panel_charts/{INIT_YMD}/model_gdps/15km/00/{FH:03d}/{FNAME}"


def test_get_4panel_key_rdps():
    ra = WX4PanelChartAddresser(init_ymd=INIT_YMD, init_hh=INIT_HH, model=ECCCModel.RDPS)
    result = ra.get_4panel_key(fh=FH, fname=FNAME)
    assert result == f"wx_4panel_charts/{INIT_YMD}/model_rdps/10km/00/{FH:03d}/{FNAME}"


def test_get_grib_key_gdps_is_lowercase():
    ra = WX4PanelChartAddresser(init_ymd=INIT_YMD, init_hh=INIT_HH, model=ECCCModel.GDPS)
    result = ra.get_grib_key(fh=FH, fname=GRIB_NAME)
    assert result == f"weather_models/{INIT_YMD}/model_gdps/15km/{INIT_HH}/{FH:03d}/{GRIB_NAME.lower()}"


def test_get_grib_key_rdps_is_lowercase():
    ra = WX4PanelChartAddresser(init_ymd=INIT_YMD, init_hh=INIT_HH, model=ECCCModel.RDPS)
    result = ra.get_grib_key(fh=FH, fname=GRIB_NAME)
    assert result == f"weather_models/{INIT_YMD}/model_rdps/10km/{INIT_HH}/{FH:03d}/{GRIB_NAME.lower()}"
