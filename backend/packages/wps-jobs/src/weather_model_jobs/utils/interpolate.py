from datetime import datetime
import logging
from typing import Optional

import numpy as np

from wps_shared.db.models.weather_models import ModelRunPrediction


SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10", "apcp_sfc_0")

logger = logging.getLogger(__name__)


def interpolate_between_two_points(
    x1: float, x2: float, y1: Optional[float], y2: Optional[float], xn: float
) -> Optional[float]:
    """Interpolate values between two points in time.
    :param x1: X coordinate of the 1st value.
    :param x2: X coordinate of the 2nd value.
    :param y1: value at the 1st timestamp.
    :param y2: value at the 2nd timestamp.
    :param xn: The c coordinate we want values for.
    :return: Interpolated value.

    """
    # Bias-adjustment predictions may be unavailable, leaving either value as None.
    # Missing values cannot be interpolated, so return None.
    if y1 is None or y2 is None:
        return None

    # numpy.interp expects the x coordinates to be increasing. Keep each x paired
    # with its y value if the points were passed in reverse order.
    if x1 <= x2:
        x_axis = [x1, x2]
        y_axis = [y1, y2]
    else:
        x_axis = [x2, x1]
        y_axis = [y2, y1]

    # Unlike interp1d, numpy.interp allows values outside the x range. Keep the
    # previous behavior of raising an error when the target is not between points.
    if not x_axis[0] <= xn <= x_axis[1]:
        raise ValueError("Interpolation target must be between the two x coordinates")

    # Ensure the return value is a float after interpolation.
    return float(np.interp(xn, x_axis, y_axis))


def interpolate_bearing(
    time_a: datetime,
    time_b: datetime,
    target_time: datetime,
    direction_a: Optional[float],
    direction_b: Optional[float],
) -> Optional[float]:
    """Interpolate between two bearings, along the acute angle between the two bearings.

    params:
    :time_a: Time of the first bearing.
    :time_b: Time of the 2nd bearing.
    :target_time: Time for which we desire a value.
    :direction_a: Bearing (in degrees) at time_a, within the range [0,360)
    :direction_b: Bearing (in degrees) at time b, within the range [0,360)
    """
    # A direction can be missing if its bias-adjustment prediction is unavailable.
    # Missing values cannot be interpolated, so return None.
    if direction_a is None or direction_b is None:
        return None

    timestamp_a = time_a.timestamp()
    timestamp_b = time_b.timestamp()
    target_timestamp = target_time.timestamp()

    # Direct interpolation can take the long way around the compass.
    # If the bearings are more than 180 degrees apart, add 360 to the smaller
    # one to interpolate across north (e.g. 350 to 10 becomes 350 to 370).
    if abs(direction_a - direction_b) > 180:
        if direction_a < direction_b:
            direction_a += 360
        else:
            direction_b += 360

    # numpy.interp expects the x coordinates to be increasing. Keep each x paired
    # with its y value if the points were passed in reverse order.
    if timestamp_a <= timestamp_b:
        x_axis = [timestamp_a, timestamp_b]
        y_axis = [direction_a, direction_b]
    else:
        x_axis = [timestamp_b, timestamp_a]
        y_axis = [direction_b, direction_a]

    # Unlike interp1d, numpy.interp allows values outside the x range. Keep the
    # previous behavior of raising an error when the target is not between points.
    if not x_axis[0] <= target_timestamp <= x_axis[1]:
        raise ValueError("Interpolation target must be between the two times")

    # Perform the interpolation and ensure the result is a float.
    interpolated_value = float(np.interp(target_timestamp, x_axis, y_axis))

    # Normalize the result to the [0, 360) degree range.
    return interpolated_value % 360


def interpolate_wind_direction(prediction_a: ModelRunPrediction, prediction_b: ModelRunPrediction, target_timestamp: datetime):
    """Interpolate wind direction"""
    if prediction_a.wdir_tgl_10 is None or prediction_b.wdir_tgl_10 is None:
        # There's nothing to interpolate!
        return None

    interpolated_wdir = interpolate_bearing(prediction_a.prediction_timestamp, prediction_b.prediction_timestamp, target_timestamp, prediction_a.wdir_tgl_10, prediction_b.wdir_tgl_10)

    return interpolated_wdir


def construct_interpolated_noon_prediction(prediction_a: ModelRunPrediction, prediction_b: ModelRunPrediction, model_keys):
    """Construct a noon prediction by interpolating."""
    # create a noon prediction. (using utc hour 20, as that is solar noon in B.C.)
    noon_prediction = ModelRunPrediction()
    noon_prediction.prediction_timestamp = prediction_a.prediction_timestamp.replace(hour=20)

    # inherit metadata
    noon_prediction.station_code = prediction_a.station_code
    noon_prediction.prediction_model_run_timestamp_id = prediction_a.prediction_model_run_timestamp_id

    # throw timestamps into their own variables.
    timestamp_a = prediction_a.prediction_timestamp.timestamp()
    timestamp_b = prediction_b.prediction_timestamp.timestamp()
    noon_timestamp = noon_prediction.prediction_timestamp.timestamp()
    # calculate interpolated values.
    for key in model_keys:
        value_a = getattr(prediction_a, key)
        value_b = getattr(prediction_b, key)
        if value_a is None or value_b is None:
            logger.warning("can't interpolate between None values for %s", key)
            continue

        value = interpolate_between_two_points(timestamp_a, timestamp_b, value_a, value_b, noon_timestamp)
        assert isinstance(value, float)
        setattr(noon_prediction, key, value)
    if noon_prediction.apcp_sfc_0 is None or prediction_a.apcp_sfc_0 is None:
        noon_prediction.delta_precip = None
    else:
        noon_prediction.delta_precip = noon_prediction.apcp_sfc_0 - prediction_a.apcp_sfc_0

    noon_prediction.wdir_tgl_10 = interpolate_wind_direction(prediction_a, prediction_b, noon_prediction.prediction_timestamp)

    return noon_prediction
