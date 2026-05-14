import sys
from unittest.mock import MagicMock, patch

import pytest
from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel


# Patch all plotter imports before importing the module under test
@pytest.fixture(autouse=True)
def mock_plotters():
    """Mock all external plotter functions to isolate PlotterFactory logic.

    plotter_factory.py captures function references into PLOTTER_REGISTRY at
    import time, so the cached module must be evicted before each test to force
    a fresh import that picks up this test's specific mock objects.
    """
    sys.modules.pop("wps_weather.wx_4panel_charts.plotter_factory", None)
    with patch.dict(
        "sys.modules",
        {
            "wps_weather.wx_4panel_charts.plot_500mb": MagicMock(plot_500hpa=MagicMock()),
            "wps_weather.wx_4panel_charts.plot_500mb_rdps": MagicMock(plot_500hpa=MagicMock()),
            "wps_weather.wx_4panel_charts.plot_700mb": MagicMock(plot_700hpa=MagicMock()),
            "wps_weather.wx_4panel_charts.plot_700mb_rdps": MagicMock(plot_700hpa_rdps=MagicMock()),
            "wps_weather.wx_4panel_charts.plot_mslp": MagicMock(plot_mslp_thickness=MagicMock()),
            "wps_weather.wx_4panel_charts.plot_mslp_rdps": MagicMock(
                plot_mslp_thickness_rdps=MagicMock()
            ),
            "wps_weather.wx_4panel_charts.plot_precip": MagicMock(plot_pcpn12=MagicMock()),
            "wps_weather.wx_4panel_charts.plot_precip_rdps": MagicMock(plot_pcpn3_rdps=MagicMock()),
        },
    ):
        yield
    sys.modules.pop("wps_weather.wx_4panel_charts.plotter_factory", None)


@pytest.fixture()
def gdps_factory():
    from wps_weather.wx_4panel_charts.plotter_factory import PlotterFactory

    return PlotterFactory(ECCCModel.GDPS)


@pytest.fixture()
def rdps_factory():
    from wps_weather.wx_4panel_charts.plotter_factory import PlotterFactory

    return PlotterFactory(ECCCModel.RDPS)


class TestPlotterFactoryInit:
    def test_gdps_initialises_successfully(self, gdps_factory):
        assert gdps_factory is not None

    def test_rdps_initialises_successfully(self, rdps_factory):
        assert rdps_factory is not None

    def test_unsupported_model_raises_value_error(self, mock_plotters):
        from wps_weather.wx_4panel_charts.plotter_factory import PlotterFactory

        with pytest.raises(ValueError, match="Unsupported model"):
            PlotterFactory("UNSUPPORTED_MODEL")

    def test_none_model_raises_value_error(self, mock_plotters):
        from wps_weather.wx_4panel_charts.plotter_factory import PlotterFactory

        with pytest.raises(ValueError, match="Unsupported model"):
            PlotterFactory(None)


class TestGdpsPlotters:
    def test_get_500hpa_plotter_returns_callable(self, gdps_factory):
        assert callable(gdps_factory.get_500hpa_plotter())

    def test_get_700hpa_plotter_returns_callable(self, gdps_factory):
        assert callable(gdps_factory.get_700hpa_plotter())

    def test_get_mslp_thickness_plotter_returns_callable(self, gdps_factory):
        assert callable(gdps_factory.get_mslp_thickness_plotter())

    def test_get_pcpn_plotter_returns_callable(self, gdps_factory):
        assert callable(gdps_factory.get_pcpn_plotter())

    def test_get_500hpa_plotter_is_gdps_implementation(self, gdps_factory):
        from wps_weather.wx_4panel_charts import plot_500mb

        assert gdps_factory.get_500hpa_plotter() is plot_500mb.plot_500hpa

    def test_get_700hpa_plotter_is_gdps_implementation(self, gdps_factory):
        from wps_weather.wx_4panel_charts import plot_700mb

        assert gdps_factory.get_700hpa_plotter() is plot_700mb.plot_700hpa

    def test_get_mslp_thickness_plotter_is_gdps_implementation(self, gdps_factory):
        from wps_weather.wx_4panel_charts import plot_mslp

        assert gdps_factory.get_mslp_thickness_plotter() is plot_mslp.plot_mslp_thickness

    def test_get_pcpn_plotter_is_gdps_implementation(self, gdps_factory):
        from wps_weather.wx_4panel_charts import plot_precip

        assert gdps_factory.get_pcpn_plotter() is plot_precip.plot_pcpn12


class TestRdpsPlotters:
    def test_get_500hpa_plotter_returns_callable(self, rdps_factory):
        assert callable(rdps_factory.get_500hpa_plotter())

    def test_get_700hpa_plotter_returns_callable(self, rdps_factory):
        assert callable(rdps_factory.get_700hpa_plotter())

    def test_get_mslp_thickness_plotter_returns_callable(self, rdps_factory):
        assert callable(rdps_factory.get_mslp_thickness_plotter())

    def test_get_pcpn_plotter_returns_callable(self, rdps_factory):
        assert callable(rdps_factory.get_pcpn_plotter())

    def test_get_500hpa_plotter_is_rdps_implementation(self, rdps_factory):
        from wps_weather.wx_4panel_charts import plot_500mb_rdps

        assert rdps_factory.get_500hpa_plotter() is plot_500mb_rdps.plot_500hpa

    def test_get_700hpa_plotter_is_rdps_implementation(self, rdps_factory):
        from wps_weather.wx_4panel_charts import plot_700mb_rdps

        assert rdps_factory.get_700hpa_plotter() is plot_700mb_rdps.plot_700hpa_rdps

    def test_get_mslp_thickness_plotter_is_rdps_implementation(self, rdps_factory):
        from wps_weather.wx_4panel_charts import plot_mslp_rdps

        assert rdps_factory.get_mslp_thickness_plotter() is plot_mslp_rdps.plot_mslp_thickness_rdps

    def test_get_pcpn_plotter_is_rdps_implementation(self, rdps_factory):
        from wps_weather.wx_4panel_charts import plot_precip_rdps

        assert rdps_factory.get_pcpn_plotter() is plot_precip_rdps.plot_pcpn3_rdps


class TestPlotterRegistryIsolation:
    def test_gdps_and_rdps_500hpa_plotters_are_distinct(self, gdps_factory, rdps_factory):
        assert gdps_factory.get_500hpa_plotter() is not rdps_factory.get_500hpa_plotter()

    def test_gdps_and_rdps_700hpa_plotters_are_distinct(self, gdps_factory, rdps_factory):
        assert gdps_factory.get_700hpa_plotter() is not rdps_factory.get_700hpa_plotter()

    def test_gdps_and_rdps_mslp_plotters_are_distinct(self, gdps_factory, rdps_factory):
        assert (
            gdps_factory.get_mslp_thickness_plotter()
            is not rdps_factory.get_mslp_thickness_plotter()
        )

    def test_gdps_and_rdps_pcpn_plotters_are_distinct(self, gdps_factory, rdps_factory):
        assert gdps_factory.get_pcpn_plotter() is not rdps_factory.get_pcpn_plotter()

    def test_same_model_returns_same_plotter_instance(self):
        from wps_weather.wx_4panel_charts.plotter_factory import PlotterFactory

        factory_a = PlotterFactory(ECCCModel.GDPS)
        factory_b = PlotterFactory(ECCCModel.GDPS)
        assert factory_a.get_500hpa_plotter() is factory_b.get_500hpa_plotter()