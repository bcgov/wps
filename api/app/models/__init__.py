""" Code common to app.models.fetch """
from enum import Enum
from typing import List
from scipy.interpolate import interp1d
from app.db.models import ModelRunGridSubsetPrediction


# Key values on ModelRunGridSubsetPrediction.
MODEL_VALUE_KEYS = ('tmp_tgl_2', 'rh_tgl_2')


class ModelEnum(str, Enum):
    """ Enumerator for different kinds of supported weather models """
    GDPS = 'GDPS'
    RDPS = 'RDPS'


def interpolate_between_two_points(
        point_a: int, point_b: int, value_a: List[float], value_b: List[float], point_of_interest: int):
    """ Interpolate values between two points in time.
    :param timestamp_a: Timestamp of the 1st value.
    :param timestamp_b: Timestamp of the 2nd value.
    :param value_a: List of values at the 1st timestamp.
    :param value_b: List of values at the 2nd timestamp.
    :param point_of_interest: The point we want values for.
    :return: Interpolated values.

    """
    # Prepare x-axis (time).
    x_axis = [point_a, point_b]
    # Prepare y-axis (values).
    y_axis = [
        [value_a[0], value_b[0]],
        [value_a[1], value_b[1]],
        [value_a[2], value_b[2]],
        [value_a[3], value_b[3]]
    ]

    # Create interpolation function.
    function = interp1d(x_axis, y_axis, kind='linear')
    # Use iterpolation function to derive values at the time of interest.
    return function(point_of_interest)


def construct_interpolated_noon_prediction(prediction_a: ModelRunGridSubsetPrediction,
                                           prediction_b: ModelRunGridSubsetPrediction):
    """ Construct a noon prediction by interpolating.
    """
    # create a noon prediction. (using utc hour 20, as that is solar noon in B.C.)
    noon_prediction = ModelRunGridSubsetPrediction()
    noon_prediction.prediction_timestamp = prediction_a.prediction_timestamp.replace(
        hour=20)
    # throw timestamps into their own variables.
    timestamp_a = prediction_a.prediction_timestamp.timestamp()
    timestamp_b = prediction_b.prediction_timestamp.timestamp()
    noon_timestamp = noon_prediction.prediction_timestamp.timestamp()
    # calculate interpolated values.
    for key in MODEL_VALUE_KEYS:
        value = interpolate_between_two_points(
            timestamp_a, timestamp_b, getattr(prediction_a, key),
            getattr(prediction_b, key), noon_timestamp)
        setattr(noon_prediction, key, value)
    return noon_prediction
