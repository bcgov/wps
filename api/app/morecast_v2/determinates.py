
from functools import reduce
from itertools import groupby
import operator
from typing import Dict, List
from app.schemas.morecast_v2 import WeatherIndeterminate


class DisjointDeterminates:
    def __init__(self, actuals: List[WeatherIndeterminate], predictions: List[WeatherIndeterminate]):
        self.actuals = actuals
        self.predictions = predictions


class AllDisjointDeterminates:
    disjoint_determinates: Dict[int, DisjointDeterminates]

    def __init__(self):
        self.disjoint_determinates = {}

    def set(self, station_code: int, determinates: DisjointDeterminates):
        self.disjoint_determinates[station_code] = determinates

    def size(self):
        return len(self.disjoint_determinates)

    def get_flat_actuals(self):
        all_actuals = [d.actuals for d in self.disjoint_determinates.values()]
        return reduce(lambda actuals1, actuals2: actuals1 + actuals2, all_actuals)

    def get_flat_predictions(self):
        all_predictions = [d.predictions for d in self.disjoint_determinates.values()]
        return reduce(lambda predictions1, predictions2: predictions1 + predictions2, all_predictions)


def get_all_disjoint_determinates(actuals: List[WeatherIndeterminate],
                                  predictions: List[WeatherIndeterminate]) -> AllDisjointDeterminates:
    """ Returns of actuals and predictions that are disjointed 
    and ordered ascendingly by date. Assumes all input lists are defined by the
     same set of stations. """
    station_codes = list(set([actual.station_code for actual in actuals] +
                             [prediction.station_code for prediction in predictions]))

    actuals_by_station_code = group_by_station_code(actuals)
    predictions_by_station_code = group_by_station_code(predictions)

    all_determinates: AllDisjointDeterminates = AllDisjointDeterminates()

    for station_code in station_codes:
        actuals_for_station = actuals_by_station_code.get(station_code, [])
        predictions_for_station = predictions_by_station_code.get(station_code, [])
        disjoint_determinates = get_disjoint_determinates(
            actuals_for_station, predictions_for_station)
        all_determinates.set(station_code, disjoint_determinates)

    return all_determinates


def group_by_station_code(weather_indeterminates: List[WeatherIndeterminate]):
    # Sorting dailies into dict keyed by station code
    key = operator.attrgetter('station_code')
    by_station_code = dict((k, list(map(lambda x: x, values)))
                           for k, values in groupby(sorted(weather_indeterminates, key=key), key))
    return by_station_code


def get_disjoint_determinates(actuals_for_station: List[WeatherIndeterminate],
                              predictions_for_station: List[WeatherIndeterminate]) -> DisjointDeterminates:
    if len(actuals_for_station) == 0:
        return DisjointDeterminates(actuals=[], predictions=predictions_for_station)

    latest_actual_date = max([x.utcTimestamp for x in actuals_for_station]).date()

    future_predictions_for_station = [prediction for prediction in predictions_for_station if prediction.utcTimestamp.date()
                                      > latest_actual_date]
    return DisjointDeterminates(actuals=actuals_for_station,
                                predictions=future_predictions_for_station)
