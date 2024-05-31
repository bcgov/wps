from datetime import datetime
import logging
from scipy.interpolate import interp1d
from app.db.models.weather_models import ModelRunPrediction


SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10", "apcp_sfc_0")

logger = logging.getLogger(__name__)


def interpolate_between_two_points(
        x1: int, x2: int, y1: float, y2: float, xn: int) -> float:
    """ Interpolate values between two points in time.
    :param x1: X coordinate of the 1st value.
    :param x2: X coordinate of the 2nd value.
    :param y1: value at the 1st timestamp.
    :param y2: value at the 2nd timestamp.
    :param xn: The c coordinate we want values for.
    :return: Interpolated value.

    """
    # Prepare x-axis (time).
    x_axis = [x1, x2]
    # Prepare y-axis (values).
    y_axis = [y1, y2]

    # Create interpolation function.
    linear_interp = interp1d(x_axis, y_axis, kind='linear')
    # Use iterpolation function to derive values at the time of interest.
    return linear_interp(xn).item()


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
            y_axis = (direction_a + 360, direction_b)
        else:
            y_axis = (direction_a, direction_b + 360)
    else:
        y_axis = (direction_a, direction_b)

    linear_interp = interp1d(x_axis, y_axis, kind='linear')
    interpolated_value = linear_interp(target_time.timestamp()).item(0)
    if interpolated_value >= 360:
        # If we had to adjust the angles, we need to re-adjust the resultant angle.
        return interpolated_value - 360
    return interpolated_value


def interpolate_wind_direction(prediction_a: ModelRunPrediction,
                               prediction_b: ModelRunPrediction,
                               target_timestamp: datetime):
    """ Interpolate wind direction  """
    if prediction_a.wdir_tgl_10 is None or prediction_b.wdir_tgl_10 is None:
        # There's nothing to interpolate!
        return None

    interpolated_wdir = interpolate_bearing(prediction_a.prediction_timestamp,
                                            prediction_b.prediction_timestamp, target_timestamp,
                                            prediction_a.wdir_tgl_10, prediction_b.wdir_tgl_10)

    return interpolated_wdir


def construct_interpolated_noon_prediction(prediction_a: ModelRunPrediction,
                                           prediction_b: ModelRunPrediction,
                                           model_keys):
    """ Construct a noon prediction by interpolating.
    """
    # create a noon prediction. (using utc hour 20, as that is solar noon in B.C.)
    noon_prediction = ModelRunPrediction()
    noon_prediction.prediction_timestamp = prediction_a.prediction_timestamp.replace(
        hour=20)
    # throw timestamps into their own variables.
    timestamp_a = prediction_a.prediction_timestamp.timestamp()
    timestamp_b = prediction_b.prediction_timestamp.timestamp()
    noon_timestamp = noon_prediction.prediction_timestamp.timestamp()
    # calculate interpolated values.
    for key in model_keys:
        value_a = getattr(prediction_a, key)
        value_b = getattr(prediction_b, key)
        if value_a is None or value_b is None:
            logger.warning('can\'t interpolate between None values for %s', key)
            continue

        value = interpolate_between_two_points(timestamp_a, timestamp_b, value_a, value_b, noon_timestamp)
        assert isinstance(value, float)
        setattr(noon_prediction, key, value)
    if noon_prediction.apcp_sfc_0 is None or prediction_a.apcp_sfc_0 is None:
        noon_prediction.delta_precip = None
    else:
        noon_prediction.delta_precip = noon_prediction.apcp_sfc_0 - prediction_a.apcp_sfc_0

    noon_prediction.wdir_tgl_10 = interpolate_wind_direction(
        prediction_a, prediction_b, noon_prediction.prediction_timestamp)

    return noon_prediction