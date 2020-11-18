""" Some crud responses used to mock our calls to app.db.crud
"""
from datetime import datetime
from app.db.models import ModelRunGridSubsetPrediction
from app.db.models.observations import HourlyActual


def get_actuals_left_outer_join_with_predictions(*args):  # pylint: disable=unused-argument
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
            ModelRunGridSubsetPrediction(
            tmp_tgl_2=[2, 3, 4, 5],
            rh_tgl_2=[10, 20, 30, 40],
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
            ModelRunGridSubsetPrediction(
            tmp_tgl_2=[1, 2, 3, 4],
            rh_tgl_2=[20, 30, 40, 50],
            prediction_timestamp=datetime(2020, 10, 10, 21))],
        # day 2
        [HourlyActual(
            weather_date=datetime(2020, 10, 11, 18),
            temperature=20,
            temp_valid=True,
            relative_humidity=50,
            rh_valid=True),
            ModelRunGridSubsetPrediction(
            tmp_tgl_2=[2, 3, 4, 5],
            rh_tgl_2=[10, 20, 30, 40],
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
            ModelRunGridSubsetPrediction(
            tmp_tgl_2=[1, 2, 3, 4],
            rh_tgl_2=[20, 30, 40, 50],
            prediction_timestamp=datetime(2020, 10, 11, 21))]
    ]
    return result
