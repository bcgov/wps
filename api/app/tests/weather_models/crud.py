""" Some crud responses used to mock our calls to app.db.crud
"""
from datetime import datetime
from app.db.models.weather_models import ModelRunPrediction, WeatherStationModelPrediction
from app.db.models.observations import HourlyActual


class MockActualPrecip:
    day: datetime
    actual_precip_24h: float

    def __init__(self, day, actual_precip_24h):
        self.day=day
        self.actual_precip_24h=actual_precip_24h


def get_actuals_left_outer_join_with_predictions(*args):
    """ Fixed response as replacement for app.db.crud.observations.get_actuals_left_outer_join_with_predictions
    """
    result = [
        # day 1
        [HourlyActual(
            weather_date=datetime(2020, 10, 10, 18),
            temperature=20,
            temp_valid=True,
            wind_speed=10,
            wind_direction=90,
            relative_humidity=50,
            rh_valid=True),
         ModelRunPrediction(
            tmp_tgl_2=2,
            rh_tgl_2=10,
            apcp_sfc_0=2,
            wind_tgl_10=11,
            wdir_tgl_10=97,
            prediction_timestamp=datetime(2020, 10, 10, 18))],
        [HourlyActual(weather_date=datetime(2020, 10, 10, 19)), None],
        [HourlyActual(weather_date=datetime(2020, 10, 10, 20),
                      temperature=25,
                      wind_speed=15,
                      wind_direction=270,
                      temp_valid=True,
                      relative_humidity=70,
                      rh_valid=True), None],
        [HourlyActual(
            weather_date=datetime(2020, 10, 10, 21),
            temperature=30,
            temp_valid=True,
            wind_speed=12,
            wind_direction=120,
            relative_humidity=100,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=1,
            rh_tgl_2=20,
            apcp_sfc_0=3,
            wind_tgl_10=11,
            wdir_tgl_10=101,
            prediction_timestamp=datetime(2020, 10, 10, 21))],
        # day 2
        [HourlyActual(
            weather_date=datetime(2020, 10, 11, 18),
            temperature=20,
            temp_valid=True,
            wind_speed=9,
            wind_direction=121,
            relative_humidity=50,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=2,
            rh_tgl_2=10,
            apcp_sfc_0=2,
            wind_tgl_10=11,
            wdir_tgl_10=110,
            prediction_timestamp=datetime(2020, 10, 11, 18))],
        [HourlyActual(weather_date=datetime(2020, 10, 11, 19)), None],
        [HourlyActual(weather_date=datetime(2020, 10, 11, 20),
                      temperature=27,
                      temp_valid=True,
                      wind_speed=10,
                      wind_direction=98,
                      relative_humidity=60,
                      rh_valid=True), None],
        [HourlyActual(
            weather_date=datetime(2020, 10, 11, 21),
            temperature=30,
            wind_speed=9,
            wind_direction=118,
            temp_valid=True,
            relative_humidity=100,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=1,
            rh_tgl_2=20,
            apcp_sfc_0=3,
            wind_tgl_10=10,
            wdir_tgl_10=111,
            prediction_timestamp=datetime(2020, 10, 11, 21))]
    ]
    return result

def get_accumulated_precip_by_24h_interval(*args):
    """ Fixed response as replacement for app.db.crud.observations.get_accumulated_precip_by_24h_interval
    """
    return [
        MockActualPrecip(
            day=datetime(2023,10,10,20,0,0),
            actual_precip_24h=3

        ),
        MockActualPrecip(
            day=datetime(2023,10,11,20,0,0),
            actual_precip_24h=3
        )
    ]


def get_predicted_daily_precip(*args):
    return [
        WeatherStationModelPrediction(
            bias_adjusted_precip_24h=None,
            precip_24h=3,
            prediction_timestamp=datetime(2023,10,10,20,0,0)
        ),
        WeatherStationModelPrediction(
            bias_adjusted_precip_24h=None,
            precip_24h=3,
            prediction_timestamp=datetime(2023,10,11,20,0,0)
        )
    ]
