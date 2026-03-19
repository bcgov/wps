from wps_weather.wx_4panel_charts.plot_500mb import plot_500hpa as plot_500hpa_gdps
from wps_weather.wx_4panel_charts.plot_500mb_rdps import plot_500hpa as plot_500hpa_rdps
from wps_weather.wx_4panel_charts.plot_700mb import plot_700hpa as plot_700hpa_gdps
from wps_weather.wx_4panel_charts.plot_700mb_rdps import plot_700hpa_rdps
from wps_weather.wx_4panel_charts.plot_mslp import plot_mslp_thickness as plot_mslp_thickness_gdps
from wps_weather.wx_4panel_charts.plot_mslp_rdps import plot_mslp_thickness_rdps
from wps_weather.wx_4panel_charts.plot_precip import plot_pcpn12 as plot_pcpn12_gdps
from wps_weather.wx_4panel_charts.plot_precip_rdps import plot_pcpn3_rdps
from wps_weather.wx_4panel_charts.raster_addresser import ECCCModel


class PlotterProvider:
    """
    A helper class that return the appropriate chart plotters for the specified model.
    """
    def __init__(self, model: ECCCModel):
        if model not in [ECCCModel.GDPS, ECCCModel.RDPS]:
            raise ValueError(f"Model must be one of GDPS or RDPS, received {model}")
        self.model = model

    def get_500hpa_plotter(self):
        return plot_500hpa_gdps if self.model == ECCCModel.GDPS else plot_500hpa_rdps

    def get_700hpa_plotter(self):
        return plot_700hpa_gdps if self.model == ECCCModel.GDPS else plot_700hpa_rdps

    def get_mslp_thickness_plotter(self):
        return (
            plot_mslp_thickness_gdps if self.model == ECCCModel.GDPS else plot_mslp_thickness_rdps
        )

    def get_pcpn_plotter(self):
        return plot_pcpn12_gdps if self.model == ECCCModel.GDPS else plot_pcpn3_rdps
