import logging
import numpy as np
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class WindDirectionSamples:
    """ Class for storing samples in buckets of hours.
    e.g. a temperature sample consists of an x axis (predicted values) and a y axis (observed values) put
    together in hour buckets.
    """

    def __init__(self):
        self._x = defaultdict(list)
        self._y = defaultdict(list)

    def hours(self):
        """ Return all the hours used to bucket samples together. """
        return self._x.keys()

    def append_x(self, value, timestamp: datetime):
        """ Append another predicted value. """
        self._x[timestamp.hour].append(value)

    def append_y(self, value, timestamp: datetime):
        """ Append another observered values. """
        self._y[timestamp.hour].append(value)

    def np_x(self, hour):
        """ Return numpy array of the predicted values, reshaped appropriately. """
        return np.array(self._x[hour])

    def np_y(self, hour):
        """ Return a numpy array of the observed values """
        return np.array(self._y[hour])

    def add_sample(self,
                   model_value: float,
                   actual_value: float,
                   timestamp: datetime,
                   model_key: str,
                   sample_key: str):
        """ Add a sample, interpolating the model values spatially """
        # Additional logging to assist with finding errors:
        logger.info('adding sample for %s->%s with: model_values %s, actual_value: %s',
                    model_key, sample_key, model_value, actual_value)
        # Add to the data we're going to learn from:
        # Using two variables, the interpolated temperature value, and the hour of the day.
        self.append_x(model_value, timestamp)
        self.append_y(actual_value, timestamp)
