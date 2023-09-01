import logging
import math
from typing import Optional, Callable
import pandas as pd
from dataclasses import dataclass

from app.utils.singleton import Singleton

logger = logging.getLogger(__name__)


@dataclass
class Comparator:
    result: float
    fn: Callable[[float], bool]


@dataclass
class RHRangeFFMC:
    """ 
        Describes the range conditions for RH.
        Applies below then between comparators, returning early if either are true
        otherwise returns the above value
    """
    below: Comparator
    between: Comparator
    above: float

    def for_rh(self, input_rh: float):
        if self.below.fn(input_rh):
            return self.below.result
        elif self.between.fn(input_rh):
            return self.between.result
        else:
            return self.above


@Singleton
class YesterdayDiurnalFFMCLookupTable():
    """ Dataframe singleton of the yesterday diurnal FFMC lookup table (Table 2) from 
    Diurnal Variation in the Fine Fuel Moisture Code: Tables and Computer Source Code
    Lawson et al, 1996 (https://www.for.gov.bc.ca/hfd/pubs/docs/frr/Frr245.htm).

    FFMC values are indexed by a tuple of (noon LST FFMC, LST hour).
    """

    def __init__(self):
        data = [
            # 50 range
            (50, 6, RHRangeFFMC(below=Comparator(fn=lambda x: x < 68, result=53.5),
                                between=Comparator(fn=lambda rh: rh >= 68 and rh <= 87, result=47.6),
                                above=42.9))
        ]

        column_names = ['ffmc', 'hour', 'predicted_ffmc_range']
        self.yesterday_lookup = pd.DataFrame(data, columns=column_names)
        self.yesterday_lookup.set_index(['ffmc', 'hour'], inplace=True)

    def get(self, daily_ffmc: float, hour: int, rh: float) -> Optional[float]:
        if daily_ffmc < 50:
            return None

        # Round up and clamp to 100 if somehow over 100
        lookup_ffmc = min(100, math.ceil(daily_ffmc))
        return self.yesterday_lookup.loc[(daily_ffmc, hour)]['predicted_ffmc_range'].for_rh(rh)
