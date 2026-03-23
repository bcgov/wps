import enum
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Define a minimal mock enum for use in fake modules
# (this will be used by fake_wps_modules before the real module is loaded)
class ECCCModel(str, enum.Enum):
    GDPS = "GDPS"
    RDPS = "RDPS"
    HRDPS = "HRDPS"


class FakeWPSModules:
    """Helper class to load real modules after fake modules are in place."""

    def get_config_builder_class(self):
        """Load and return the real ConfigBuilder class."""
        import importlib.util
        from pathlib import Path

        # First, we need to make sure raster_addresser has the RasterAddresser class
        src_dir = Path(__file__).resolve().parents[1] / "wx_4panel_charts"
        raster_addresser_path = src_dir / "raster_addresser.py"

        raster_spec = importlib.util.spec_from_file_location(
            "wps_weather.wx_4panel_charts.raster_addresser",
            raster_addresser_path
        )
        raster_mod = importlib.util.module_from_spec(raster_spec)
        sys.modules["wps_weather.wx_4panel_charts.raster_addresser"] = raster_mod
        raster_spec.loader.exec_module(raster_mod)

        # Now load config_builder
        config_builder_path = src_dir / "config_builder.py"

        spec = importlib.util.spec_from_file_location(
            "wps_weather.wx_4panel_charts.config_builder",
            config_builder_path
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["wps_weather.wx_4panel_charts.config_builder"] = mod
        spec.loader.exec_module(mod)

        return mod.ConfigBuilder

    def get_ECCCModel(self):
        """Return the ECCCModel class defined in conftest."""
        return ECCCModel


@pytest.fixture
def fake_wps_modules(monkeypatch):
    """
    Injects a fake wps_weather package tree with the minimal surface that
    plotter_factory.py expects:
      - wps_weather.wx_4panel_charts.plot_500mb.plot_500hpa
      - wps_weather.wx_4panel_charts.plot_500mb_rdps.plot_500hpa
      - wps_weather.wx_4panel_charts.plot_700mb.plot_700hpa
      - wps_weather.wx_4panel_charts.plot_700mb_rdps.plot_700hpa_rdps
      - wps_weather.wx_4panel_charts.plot_mslp.plot_mslp_thickness
      - wps_weather.wx_4panel_charts.plot_mslp_rdps.plot_mslp_thickness_rdps
      - wps_weather.wx_4panel_charts.plot_precip.plot_pcpn12
      - wps_weather.wx_4panel_charts.plot_precip_rdps.plot_pcpn3_rdps
    """
    # Create base packages
    wps_weather = types.ModuleType("wps_weather")
    wx_4panel_charts = types.ModuleType("wps_weather.wx_4panel_charts")
    # Make wx_4panel_charts behave like a package by setting __path__
    # This allows Python to import submodules from it
    wx_4panel_charts.__path__ = []

    # Create leaf modules with dummy functions. Provide mock return values to allow testing of the correct function being called.
    plot_500mb = types.ModuleType("wps_weather.wx_4panel_charts.plot_500mb")
    def plot_500hpa_gdps(*args, **kwargs):  # pragma: no cover - simple stub
        return (ECCCModel.GDPS, "500")
    plot_500mb.plot_500hpa = plot_500hpa_gdps

    plot_500mb_rdps = types.ModuleType("wps_weather.wx_4panel_charts.plot_500mb_rdps")
    def plot_500hpa_rdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.RDPS, "500")
    plot_500mb_rdps.plot_500hpa = plot_500hpa_rdps

    plot_700mb = types.ModuleType("wps_weather.wx_4panel_charts.plot_700mb")
    def plot_700hpa_gdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.GDPS, "700")
    plot_700mb.plot_700hpa = plot_700hpa_gdps

    plot_700mb_rdps = types.ModuleType("wps_weather.wx_4panel_charts.plot_700mb_rdps")
    def plot_700hpa_rdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.RDPS, "700")
    plot_700mb_rdps.plot_700hpa_rdps = plot_700hpa_rdps

    plot_mslp = types.ModuleType("wps_weather.wx_4panel_charts.plot_mslp")
    def plot_mslp_thickness_gdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.GDPS, "mslp_thickness")
    plot_mslp.plot_mslp_thickness = plot_mslp_thickness_gdps

    plot_mslp_rdps = types.ModuleType("wps_weather.wx_4panel_charts.plot_mslp_rdps")
    def plot_mslp_thickness_rdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.RDPS, "mslp_thickness")
    plot_mslp_rdps.plot_mslp_thickness_rdps = plot_mslp_thickness_rdps

    plot_precip = types.ModuleType("wps_weather.wx_4panel_charts.plot_precip")
    def plot_pcpn12_gdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.GDPS, "pcpn")
    plot_precip.plot_pcpn12 = plot_pcpn12_gdps

    plot_precip_rdps = types.ModuleType("wps_weather.wx_4panel_charts.plot_precip_rdps")
    def plot_pcpn3_rdps(*args, **kwargs):  # pragma: no cover
        return (ECCCModel.RDPS, "pcpn")
    plot_precip_rdps.plot_pcpn3_rdps = plot_pcpn3_rdps

    raster_addresser = types.ModuleType("wps_weather.wx_4panel_charts.raster_addresser")
    # Add the ECCCModel enum to the mock raster_addresser module
    raster_addresser.ECCCModel = ECCCModel

    # Create a fake config_builder module
    config_builder = types.ModuleType("wps_weather.wx_4panel_charts.config_builder")

    # Create a fake plotter_factory module
    plotter_factory = types.ModuleType("wps_weather.wx_4panel_charts.plotter_factory")
    # We'll populate this with actual code later in the module_under_test fixture

    # Wire the package hierarchy
    sys.modules["wps_weather"] = wps_weather
    sys.modules["wps_weather.wx_4panel_charts"] = wx_4panel_charts
    sys.modules["wps_weather.wx_4panel_charts.plot_500mb"] = plot_500mb
    sys.modules["wps_weather.wx_4panel_charts.plot_500mb_rdps"] = plot_500mb_rdps
    sys.modules["wps_weather.wx_4panel_charts.plot_700mb"] = plot_700mb
    sys.modules["wps_weather.wx_4panel_charts.plot_700mb_rdps"] = plot_700mb_rdps
    sys.modules["wps_weather.wx_4panel_charts.plot_mslp"] = plot_mslp
    sys.modules["wps_weather.wx_4panel_charts.plot_mslp_rdps"] = plot_mslp_rdps
    sys.modules["wps_weather.wx_4panel_charts.plot_precip"] = plot_precip
    sys.modules["wps_weather.wx_4panel_charts.plot_precip_rdps"] = plot_precip_rdps
    sys.modules["wps_weather.wx_4panel_charts.raster_addresser"] = raster_addresser
    sys.modules["wps_weather.wx_4panel_charts.plotter_factory"] = plotter_factory
    sys.modules["wps_weather.wx_4panel_charts.config_builder"] = config_builder

    # Expose the types on the parent package.
    wx_4panel_charts.plot_500mb = plot_500mb
    wx_4panel_charts.plot_500mb_rdps = plot_500mb_rdps
    wx_4panel_charts.plot_700mb = plot_700mb
    wx_4panel_charts.plot_700mb_rdps = plot_700mb_rdps
    wx_4panel_charts.plot_mslp = plot_mslp
    wx_4panel_charts.plot_mslp_rdps = plot_mslp_rdps
    wx_4panel_charts.plot_precip = plot_precip
    wx_4panel_charts.plot_precip_rdps = plot_precip_rdps
    wx_4panel_charts.raster_addresser = raster_addresser

    yield FakeWPSModules()  # unit tests run here

    # Cleanup
    for mod in [
        "wps_weather",
        "wps_weather.wx_4panel_charts",
        "wps_weather.wx_4panel_charts.plot_500mb",
        "wps_weather.wx_4panel_charts.plot_500mb_rdps",
        "wps_weather.wx_4panel_charts.plot_700mb",
        "wps_weather.wx_4panel_charts.plot_700mb_rdps",
        "wps_weather.wx_4panel_charts.plot_mslp",
        "wps_weather.wx_4panel_charts.plot_mslp_rdps",
        "wps_weather.wx_4panel_charts.plot_precip",
        "wps_weather.wx_4panel_charts.plot_precip_rdps",
        "wps_weather.wx_4panel_charts.raster_addresser",
        "wps_weather.wx_4panel_charts.plotter_factory",
        "wps_weather.wx_4panel_charts.config_builder",
    ]:
        sys.modules.pop(mod, None)


@pytest.fixture
def module_under_test(fake_wps_modules):
    """
    Load the actual plotter_factory module code from the real file,
    after fake modules are in place so the imports bind to our mocks.
    """
    import importlib.util

    # Find the real plotter_factory.py file
    src_dir = Path(__file__).resolve().parents[1] / "wx_4panel_charts"
    plotter_factory_path = src_dir / "plotter_factory.py"

    # Load the module from file
    spec = importlib.util.spec_from_file_location(
        "wps_weather.wx_4panel_charts.plotter_factory",
        plotter_factory_path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wps_weather.wx_4panel_charts.plotter_factory"] = mod
    spec.loader.exec_module(mod)

    return mod