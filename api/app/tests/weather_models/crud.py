""" Some crud responses used to mock our calls to app.db.crud
"""
from datetime import datetime
from app.db.models.weather_models import ModelRunPrediction
from app.db.models.observations import HourlyActual


def get_actuals_left_outer_join_with_predictions(*args):
    """ Fixed response as replacement for app.db.crud.observations.get_actuals_left_outer_join_with_predictions
    """
    result = [
        # day 1
        [HourlyActual(
            weather_date=datetime(2020, 10, 10, 18),
            temperature=20,
            temp_valid=True,
            relative_humidity=50,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=2,
            rh_tgl_2=10,
            apcp_sfc_0=2,
            prediction_timestamp=datetime(2020, 10, 10, 18))],
        [HourlyActual(weather_date=datetime(2020, 10, 10, 19)), None],
        [HourlyActual(weather_date=datetime(2020, 10, 10, 20),
                      temperature=25,
                      temp_valid=True,
                      relative_humidity=70,
                      rh_valid=True), None],
        [HourlyActual(
            weather_date=datetime(2020, 10, 10, 21),
            temperature=30,
            temp_valid=True,
            relative_humidity=100,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=1,
            rh_tgl_2=20,
            apcp_sfc_0=3,
            prediction_timestamp=datetime(2020, 10, 10, 21))],
        # day 2
        [HourlyActual(
            weather_date=datetime(2020, 10, 11, 18),
            temperature=20,
            temp_valid=True,
            relative_humidity=50,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=2,
            rh_tgl_2=10,
            apcp_sfc_0=2,
            prediction_timestamp=datetime(2020, 10, 11, 18))],
        [HourlyActual(weather_date=datetime(2020, 10, 11, 19)), None],
        [HourlyActual(weather_date=datetime(2020, 10, 11, 20),
                      temperature=27,
                      temp_valid=True,
                      relative_humidity=60,
                      rh_valid=True), None],
        [HourlyActual(
            weather_date=datetime(2020, 10, 11, 21),
            temperature=30,
            temp_valid=True,
            relative_humidity=100,
            rh_valid=True),
            ModelRunPrediction(
            tmp_tgl_2=1,
            rh_tgl_2=20,
            apcp_sfc_0=3,
            prediction_timestamp=datetime(2020, 10, 11, 21))]
    ]
    return result
