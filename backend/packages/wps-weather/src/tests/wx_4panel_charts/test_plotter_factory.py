import pytest
from wps_shared.db.models.wx_4panel_charts import ECCCModel


def test_debug_sys_path_and_packages():
    import pkgutil
    import sys

    import wps_weather  # should succeed once src is on sys.path

    print("sys.path =", sys.path)
    print("wps_weather file =", getattr(wps_weather, "__file__", None))
    print("found subpackages =", [m.name for m in pkgutil.iter_modules(wps_weather.__path__)])



def test_factory_returns_correct_functions_for_gdps(module_under_test):
    ECCCModel = module_under_test.ECCCModel
    PlotterFactory = module_under_test.PlotterFactory

    factory = PlotterFactory(ECCCModel.GDPS)

    f500 = factory.get_500hpa_plotter()
    f700 = factory.get_700hpa_plotter()
    fmslp = factory.get_mslp_thickness_plotter()
    fpcpn = factory.get_pcpn_plotter()

    # Factory should provide callables
    assert callable(f500)
    assert callable(f700)
    assert callable(fmslp)
    assert callable(fpcpn)

    # Calling the returned functions should return the mocked values
    assert f500() == (ECCCModel.GDPS, "500")
    assert f700() == (ECCCModel.GDPS, "700")
    assert fmslp() == (ECCCModel.GDPS, "mslp_thickness")
    assert fpcpn() == (ECCCModel.GDPS, "pcpn")


def test_factory_returns_correct_functions_for_rdps(module_under_test):
    PlotterFactory = module_under_test.PlotterFactory

    factory = PlotterFactory(ECCCModel.RDPS)

    f500 = factory.get_500hpa_plotter()
    f700 = factory.get_700hpa_plotter()
    fmslp = factory.get_mslp_thickness_plotter()
    fpcpn = factory.get_pcpn_plotter()

    assert callable(f500)
    assert callable(f700)
    assert callable(fmslp)
    assert callable(fpcpn)

    # And calling them should reflect our RDPS stubs
    assert f500() == (ECCCModel.RDPS, "500")
    assert f700() == (ECCCModel.RDPS, "700")
    assert fmslp() == (ECCCModel.RDPS, "mslp_thickness")
    assert fpcpn() == (ECCCModel.RDPS, "pcpn")


def test_invalid_model_raises_value_error(module_under_test):
    PlotterFactory = module_under_test.PlotterFactory

    class FakeModel:
        pass

    with pytest.raises(ValueError) as exc:
        PlotterFactory(FakeModel())
    assert "Unsupported model" in str(exc.value)


@pytest.mark.parametrize(
    "method_name, expected_key",
    [
        ("get_500hpa_plotter", "plot_500hpa"),
        ("get_700hpa_plotter", "plot_700hpa"),
        ("get_mslp_thickness_plotter", "plot_mslp_thickness"),
        ("get_pcpn_plotter", "plot_pcpn"),
    ],
)
def test_registry_contains_expected_keys(module_under_test, method_name, expected_key):
    PLOTTER_REGISTRY = module_under_test.PLOTTER_REGISTRY
    # Ensure all known models have the same required keys
    for model, mapping in PLOTTER_REGISTRY.items():
        assert expected_key in mapping, f"{expected_key} missing for model {model}"

    # Smoke test: method exists on factory
    assert hasattr(module_under_test.PlotterFactory, method_name)


def test_plotter_types_are_callable(module_under_test):
    """Ensure returned objects conform to being callable (Protocol/duck-typed)."""
    ECCCModel = module_under_test.ECCCModel
    factory = module_under_test.PlotterFactory(ECCCModel.GDPS)

    for fn in [
        factory.get_500hpa_plotter(),
        factory.get_700hpa_plotter(),
        factory.get_mslp_thickness_plotter(),
        factory.get_pcpn_plotter(),
    ]:
        assert callable(fn)