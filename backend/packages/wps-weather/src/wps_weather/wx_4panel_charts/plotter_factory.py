from typing import Any, Mapping, Protocol, TypedDict

from wps_shared.db.models.wx_4panel_charts import ECCCModel

from wps_weather.wx_4panel_charts.plot_500mb import plot_500hpa as plot_500hpa_gdps
from wps_weather.wx_4panel_charts.plot_500mb_rdps import plot_500hpa as plot_500hpa_rdps
from wps_weather.wx_4panel_charts.plot_700mb import plot_700hpa as plot_700hpa_gdps
from wps_weather.wx_4panel_charts.plot_700mb_rdps import plot_700hpa_rdps
from wps_weather.wx_4panel_charts.plot_mslp import plot_mslp_thickness as plot_mslp_thickness_gdps
from wps_weather.wx_4panel_charts.plot_mslp_rdps import plot_mslp_thickness_rdps
from wps_weather.wx_4panel_charts.plot_precip import plot_pcpn12 as plot_pcpn12_gdps
from wps_weather.wx_4panel_charts.plot_precip_rdps import plot_pcpn3_rdps


class PlotterFn(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> None: ...


class Plotters(TypedDict):
    plot_500hpa: PlotterFn
    plot_700hpa: PlotterFn
    plot_mslp_thickness: PlotterFn
    plot_pcpn: PlotterFn


PLOTTER_REGISTRY: Mapping[ECCCModel, Plotters] = {
    ECCCModel.GDPS: {
        "plot_500hpa": plot_500hpa_gdps,
        "plot_700hpa": plot_700hpa_gdps,
        "plot_mslp_thickness": plot_mslp_thickness_gdps,
        "plot_pcpn": plot_pcpn12_gdps,
    },
    ECCCModel.RDPS: {
        "plot_500hpa": plot_500hpa_rdps,
        "plot_700hpa": plot_700hpa_rdps,
        "plot_mslp_thickness": plot_mslp_thickness_rdps,
        "plot_pcpn": plot_pcpn3_rdps,
    },
}


class PlotterFactory:
    """Return appropriate chart plotters for the specified model via a central registry."""

    def __init__(self, model: ECCCModel):
        try:
            self._plotters = PLOTTER_REGISTRY[model]
        except KeyError:
            raise ValueError(f"Unsupported model: {model}")

    def get_500hpa_plotter(self) -> PlotterFn:
        return self._plotters["plot_500hpa"]

    def get_700hpa_plotter(self) -> PlotterFn:
        return self._plotters["plot_700hpa"]

    def get_mslp_thickness_plotter(self) -> PlotterFn:
        return self._plotters["plot_mslp_thickness"]

    def get_pcpn_plotter(self) -> PlotterFn:
        return self._plotters["plot_pcpn"]
