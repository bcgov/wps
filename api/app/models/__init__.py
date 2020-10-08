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
    HRDPS = 'HRDPS'


class ProjectionEnum(str, Enum):
    """ Enumerator for different projections based on the different
    kinds of weather models
    """
    LATLON_15X_15 = 'latlon.15x.15'
    HIGH_RES_CONTINENTAL = 'ps2.5km'


def interpolate_between_two_points(  # pylint: disable=invalid-name
        x1: int, x2: int, y1: List[float], y2: List[float], xn: int):
    """ Interpolate values between two points in time.
    :param x1: X coordinate of the 1st value.
    :param x2: X coordinate of the 2nd value.
    :param y1: List of values at the 1st timestamp.
    :param y2: List of values at the 2nd timestamp.
    :param xn: The c coordinate we want values for.
    :return: Interpolated values.

    """
    # Prepare x-axis (time).
    x_axis = [x1, x2]
    # Prepare y-axis (values).
    y_axis = [
        [y1[0], y2[0]],
        [y1[1], y2[1]],
        [y1[2], y2[2]],
        [y1[3], y2[3]]
    ]

    # Create interpolation function.
    function = interp1d(x_axis, y_axis, kind='linear')
    # Use iterpolation function to derive values at the time of interest.
    return function(xn)


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
