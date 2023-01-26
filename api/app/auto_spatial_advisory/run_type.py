from enum import Enum


class RunType(Enum):
    FORECAST = 'forecast'
    ACTUAL = 'actual'

    @staticmethod
    def from_str(label):
        if label in ('forecast', 'Forecast', 'FORECAST'):
            return RunType.FORECAST
        elif label in ('actual', 'Actual', 'ACTUAL'):
            return RunType.ACTUAL
        else:
            raise NotImplementedError
