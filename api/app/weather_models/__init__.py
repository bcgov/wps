""" Code common to app.weather_models.fetch """
import math
from datetime import datetime
from enum import Enum
from typing import List
import logging
from scipy.interpolate import interp1d
from app.db.models import ModelRunGridSubsetPrediction

logger = logging.getLogger(__name__)


# Key values on ModelRunGridSubsetPrediction.
# Wind direction (wdir_tgl_10_b) is handled slightly differently, so not included here.
SCALAR_MODEL_VALUE_KEYS = ('tmp_tgl_2', 'rh_tgl_2', 'apcp_sfc_0', 'wind_tgl_10')


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
    REGIONAL_PS = 'ps10km'


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


def interpolate_bearing(time_a: datetime, time_b: datetime, target_time: datetime,
                        direction_a: float, direction_b: float):
    """ Interpolate between two bearings, along the acute angle between the two bearings.

    params:
    :time_a: Time of the first bearing.
    :time_b: Time of the 2nd bearing.
    :target_Time: Time for which we desire a value.
    :direction_a: Bearing (in degrees) at time_a.
    :direction_b: Bearing (in degrees) at time b.
    """
    x_axis = (time_a.timestamp(), time_b.timestamp())
    # If the difference between two angles exceeds 180 degrees, it means we need to add
    # 360 degrees to the smaller number in order to find the actute angle.
    # After interpolating between the two angles, we need to subtract 360 degrees to ensure
    # we have a value between between 0 and 360 again.
    # e.g. a = 259 and b = 1 ; We don't actually want to interpolate between 259 and 1, we want
    # to interpolat between 361 and 259.
    if abs(direction_a - direction_b) > 180:
        # We want to interpolate along the acute angle between the two directions
        if direction_a < direction_b:
            y_axis = (direction_a+360, direction_b)
        else:
            y_axis = (direction_a, direction_b+360)
    else:
        y_axis = (direction_a, direction_b)

    function = interp1d(x_axis, y_axis, kind='linear')
    interpolated_value = function(target_time.timestamp()).item(0)
    if interpolated_value >= 360:
        # If we had to adjust the angles, we need to re-adjust the resultant angle.
        return interpolated_value - 360
    return interpolated_value


def interpolate_wind_direction(prediction_a: ModelRunGridSubsetPrediction,
                               prediction_b: ModelRunGridSubsetPrediction,
                               target_timestamp: datetime):
    """ Interpolate wind direction  """
    if prediction_a.wdir_tgl_10 is None or prediction_b.wdir_tgl_10 is None:
        # There's nothing to interpolate!
        return None
    result = []
    for wdir_tgl_10_a, wdir_tgl_10_b in zip(prediction_a.wdir_tgl_10, prediction_b.wdir_tgl_10):

        interpolated_wdir = interpolate_bearing(prediction_a.prediction_timestamp,
                                                prediction_b.prediction_timestamp, target_timestamp,
                                                wdir_tgl_10_a, wdir_tgl_10_b)

        result.append(interpolated_wdir)

    return result


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
    for key in SCALAR_MODEL_VALUE_KEYS:
        value_a = getattr(prediction_a, key)
        value_b = getattr(prediction_b, key)
        if value_a is None or value_b is None:
            logger.warning('can\'t interpolate between None values')
            continue

        value = interpolate_between_two_points(timestamp_a, timestamp_b, value_a, value_b, noon_timestamp)
        setattr(noon_prediction, key, value)
    if noon_prediction.apcp_sfc_0 is None or prediction_a.apcp_sfc_0 is None:
        noon_prediction.delta_precip = None
    else:
        noon_prediction.delta_precip = noon_prediction.apcp_sfc_0 - prediction_a.apcp_sfc_0

    noon_prediction.wdir_tgl_10 = interpolate_wind_direction(
        prediction_a, prediction_b, noon_prediction.prediction_timestamp)

    return noon_prediction
