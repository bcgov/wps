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


def below_68_rh(rh: float) -> bool: return rh < 68
def between_68_and_87_rh(rh: float) -> bool: return rh >= 68 and rh <= 87


def below_58_rh(rh: float) -> bool: return rh < 58
def between_58_and_77_rh(rh: float) -> bool: return rh >= 58 and rh <= 77


def below_48_rh(rh: float) -> bool: return rh < 48
def between_48_and_67_rh(rh: float) -> bool: return rh >= 48 and rh <= 77


def below_43_rh(rh: float) -> bool: return rh < 43
def between_43_and_62_rh(rh: float) -> bool: return rh >= 43 and rh <= 62


def below_38_rh(rh: float) -> bool: return rh < 38
def between_38_and_57_rh(rh: float) -> bool: return rh >= 38 and rh <= 57


def below_35_dot_5_rh(rh: float) -> bool: return rh < 35.5
def between_35_and_54_rh(rh: float) -> bool: return rh >= 35 and rh <= 54


def below_33_rh(rh: float) -> bool: return rh < 33
def between_33_and_52_rh(rh: float) -> bool: return rh >= 33 and rh <= 52


@Singleton
class YesterdayDiurnalFFMCLookupTable():
    """ Dataframe singleton of the yesterday diurnal FFMC lookup table (Table 2) from 
    Diurnal Variation in the Fine Fuel Moisture Code: Tables and Computer Source Code
    Lawson et al, 1996 (https://www.for.gov.bc.ca/hfd/pubs/docs/frr/Frr245.htm).

    FFMC values are indexed by a tuple of (noon LST FFMC, LST hour) adjusted to PDT (1 hour forward)
    """

    def __init__(self):
        data = [
            # 50 range
            (50, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=53.5),
                                between=Comparator(fn=between_68_and_87_rh, result=47.6),
                                above=42.9)),
            (50, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=56.3),
                                between=Comparator(fn=between_58_and_77_rh, result=48.7),
                                above=43.8)),

            (50, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=59.3),
                                between=Comparator(fn=between_48_and_67_rh, result=49.8),
                                above=44.8)),

            (50, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=64.4),
                                 between=Comparator(fn=between_43_and_62_rh, result=55.6),
                                 above=50.5)),

            (50, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=69.9),
                                 between=Comparator(fn=between_38_and_57_rh, result=61.9),
                                 above=56.8)),

            (50, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=75.9),
                                 between=Comparator(fn=between_35_and_54_rh, result=69),
                                 above=63.9)),

            (50, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=82.4),
                                 between=Comparator(fn=between_33_and_52_rh, result=76.9),
                                 above=71.8)),

            # 60 range
            (60, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=56.9),
                                between=Comparator(fn=between_68_and_87_rh, result=52.6),
                                above=48.5)),

            (60, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=59.7),
                                between=Comparator(fn=between_58_and_77_rh, result=53.8),
                                above=49.4)),

            (60, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=62.6),
                                between=Comparator(fn=between_48_and_67_rh, result=55.1),
                                above=50.2)),

            (60, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=67.3),
                                 between=Comparator(fn=between_43_and_62_rh, result=60.3),
                                 above=55.5)),

            (60, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=72.2),
                                 between=Comparator(fn=between_38_and_57_rh, result=66.0),
                                 above=61.4)),

            (60, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=77.6),
                                 between=Comparator(fn=between_35_and_54_rh, result=72.3),
                                 above=67.9)),

            (60, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=83.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=79.2),
                                 above=75.1)),

            # 70 range
            (70, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=61.7),
                                between=Comparator(fn=between_68_and_87_rh, result=58.4),
                                above=55.1)),

            (70, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=64.3),
                                between=Comparator(fn=between_58_and_77_rh, result=59.9),
                                above=55.9)),

            (70, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=67.0),
                                between=Comparator(fn=between_48_and_67_rh, result=61.4),
                                above=56.7)),

            (70, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=71.2),
                                 between=Comparator(fn=between_43_and_62_rh, result=66.0),
                                 above=61.5)),

            (70, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=75.6),
                                 between=Comparator(fn=between_38_and_57_rh, result=71.0),
                                 above=66.7)),

            (70, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=80.3),
                                 between=Comparator(fn=between_35_and_54_rh, result=76.4),
                                 above=72.3)),

            (70, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=85.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=82.2),
                                 above=78.4)),

            # 72 range
            (72, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=62.9),
                                between=Comparator(fn=between_68_and_87_rh, result=59.7),
                                above=56.5)),

            (72, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=65.4),
                                between=Comparator(fn=between_58_and_77_rh, result=61.3),
                                above=57.3)),

            (72, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=68.1),
                                between=Comparator(fn=between_48_and_67_rh, result=62.8),
                                above=58.2)),

            (72, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=72.1),
                                 between=Comparator(fn=between_43_and_62_rh, result=67.3),
                                 above=62.8)),

            (72, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=76.5),
                                 between=Comparator(fn=between_38_and_57_rh, result=72.1),
                                 above=67.8)),

            (72, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=81.0),
                                 between=Comparator(fn=between_35_and_54_rh, result=77.3),
                                 above=73.3)),

            (72, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=85.8),
                                 between=Comparator(fn=between_33_and_52_rh, result=82.9),
                                 above=79.1)),

            # 74 range
            (74, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=64.1),
                                between=Comparator(fn=between_68_and_87_rh, result=61.1),
                                above=58.0)),

            (74, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=66.6),
                                between=Comparator(fn=between_58_and_77_rh, result=62.7),
                                above=58.8)),

            (74, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=69.2),
                                between=Comparator(fn=between_48_and_67_rh, result=64.3),
                                above=59.7)),

            (74, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=73.2),
                                 between=Comparator(fn=between_43_and_62_rh, result=68.6),
                                 above=64.2)),

            (74, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=77.4),
                                 between=Comparator(fn=between_38_and_57_rh, result=73.3),
                                 above=69.0)),

            (74, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=81.9),
                                 between=Comparator(fn=between_35_and_54_rh, result=78.3),
                                 above=74.3)),

            (74, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=86.5),
                                 between=Comparator(fn=between_33_and_52_rh, result=83.6),
                                 above=79.8)),

            # 75 range
            (75, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=64.8),
                                between=Comparator(fn=between_68_and_87_rh, result=61.8),
                                above=58.8)),

            (75, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=67.2),
                                between=Comparator(fn=between_58_and_77_rh, result=63.4),
                                above=59.6)),

            (75, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=69.8),
                                between=Comparator(fn=between_48_and_67_rh, result=65.1),
                                above=60.5)),

            (75, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=73.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=69.3),
                                 above=64.9)),

            (75, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=77.9),
                                 between=Comparator(fn=between_38_and_57_rh, result=73.9),
                                 above=69.6)),

            (75, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=82.4),
                                 between=Comparator(fn=between_35_and_54_rh, result=79.0),
                                 above=74.9)),

            (75, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=86.8),
                                 between=Comparator(fn=between_33_and_52_rh, result=84.0),
                                 above=80.2)),

            # 76 range
            (76, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=65.5),
                                between=Comparator(fn=between_68_and_87_rh, result=62.5),
                                above=59.5)),

            (76, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=67.9),
                                between=Comparator(fn=between_58_and_77_rh, result=64.2),
                                above=60.4)),

            (76, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=70.4),
                                between=Comparator(fn=between_48_and_67_rh, result=65.9),
                                above=61.3)),

            (76, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=73.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=69.3),
                                 above=64.9)),

            (76, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=78.4),
                                 between=Comparator(fn=between_38_and_57_rh, result=74.5),
                                 above=70.2)),

            (76, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=83.0),
                                 between=Comparator(fn=between_35_and_54_rh, result=79.6),
                                 above=75.5)),

            (76, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=87.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=84.4),
                                 above=80.5)),

            # 77 range
            (77, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=66.2),
                                between=Comparator(fn=between_68_and_87_rh, result=63.3),
                                above=60.3)),

            (77, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=68.6),
                                between=Comparator(fn=between_58_and_77_rh, result=64.9),
                                above=61.2)),

            (77, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=71.0),
                                between=Comparator(fn=between_48_and_67_rh, result=66.7),
                                above=62.2)),

            (77, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=74.8),
                                 between=Comparator(fn=between_43_and_62_rh, result=70.8),
                                 above=66.4)),

            (77, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=78.9),
                                 between=Comparator(fn=between_38_and_57_rh, result=75.2),
                                 above=70.9)),

            (77, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=83.6),
                                 between=Comparator(fn=between_35_and_54_rh, result=80.3),
                                 above=76.1)),

            (77, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=87.6),
                                 between=Comparator(fn=between_33_and_52_rh, result=84.8),
                                 above=80.8)),

            # 78 range
            (78, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=66.9),
                                between=Comparator(fn=between_68_and_87_rh, result=64.0),
                                above=61.2)),

            (78, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=69.3),
                                between=Comparator(fn=between_58_and_77_rh, result=65.7),
                                above=62.1)),

            (78, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=71.6),
                                between=Comparator(fn=between_48_and_67_rh, result=67.5),
                                above=63.0)),

            (78, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=75.4),
                                 between=Comparator(fn=between_43_and_62_rh, result=71.6),
                                 above=67.1)),

            (78, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=79.4),
                                 between=Comparator(fn=between_38_and_57_rh, result=75.9),
                                 above=71.5)),

            (78, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=84.1),
                                 between=Comparator(fn=between_35_and_54_rh, result=80.9),
                                 above=76.6)),

            (78, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=87.9),
                                 between=Comparator(fn=between_33_and_52_rh, result=85.2),
                                 above=81.2)),

            # 79 range
            (79, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=67.7),
                                between=Comparator(fn=between_68_and_87_rh, result=64.8),
                                above=62.0)),

            (79, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=70.0),
                                between=Comparator(fn=between_58_and_77_rh, result=66.5),
                                above=62.9)),

            (79, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=72.3),
                                between=Comparator(fn=between_48_and_67_rh, result=68.4),
                                above=63.9)),

            (79, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=76.0),
                                 between=Comparator(fn=between_43_and_62_rh, result=72.3),
                                 above=67.9)),

            (79, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=80.0),
                                 between=Comparator(fn=between_38_and_57_rh, result=76.5),
                                 above=72.2)),

            (79, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=84.7),
                                 between=Comparator(fn=between_35_and_54_rh, result=81.5),
                                 above=77.2)),

            (79, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=88.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=85.6),
                                 above=81.5)),

            # 80 range
            (80, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=68.5),
                                between=Comparator(fn=between_68_and_87_rh, result=65.6),
                                above=62.9)),

            (80, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=70.7),
                                between=Comparator(fn=between_58_and_77_rh, result=67.4),
                                above=63.8)),

            (80, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=73.0),
                                between=Comparator(fn=between_48_and_67_rh, result=69.3),
                                above=64.8)),

            (80, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=76.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=73.1),
                                 above=68.7)),

            (80, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=80.5),
                                 between=Comparator(fn=between_38_and_57_rh, result=77.2),
                                 above=72.9)),

            (80, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=85.2),
                                 between=Comparator(fn=between_35_and_54_rh, result=82.2),
                                 above=77.8)),

            (80, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=88.6),
                                 between=Comparator(fn=between_33_and_52_rh, result=86.0),
                                 above=81.8)),

            # 81 range
            (81, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=69.4),
                                between=Comparator(fn=between_68_and_87_rh, result=66.4),
                                above=63.7)),

            (81, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=71.5),
                                between=Comparator(fn=between_58_and_77_rh, result=68.2),
                                above=64.7)),

            (81, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=78.7),
                                between=Comparator(fn=between_48_and_67_rh, result=70.1),
                                above=65.7)),

            (81, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=77.3),
                                 between=Comparator(fn=between_43_and_62_rh, result=73.9),
                                 above=69.5)),

            (81, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=81.1),
                                 between=Comparator(fn=between_38_and_57_rh, result=77.9),
                                 above=73.6)),

            (81, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=85.8),
                                 between=Comparator(fn=between_35_and_54_rh, result=82.8),
                                 above=78.4)),

            (81, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=88.9),
                                 between=Comparator(fn=between_33_and_52_rh, result=86.4),
                                 above=82.1)),

            # 82 range
            (82, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=70.2),
                                between=Comparator(fn=between_68_and_87_rh, result=67.2),
                                above=64.6)),

            (82, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=72.3),
                                between=Comparator(fn=between_58_and_77_rh, result=69.1),
                                above=65.7)),

            (82, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=74.5),
                                between=Comparator(fn=between_48_and_67_rh, result=71.1),
                                above=66.7)),

            (82, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=78.0),
                                 between=Comparator(fn=between_43_and_62_rh, result=74.8),
                                 above=70.4)),

            (82, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=81.8),
                                 between=Comparator(fn=between_38_and_57_rh, result=78.7),
                                 above=74.3)),

            (82, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=86.3),
                                 between=Comparator(fn=between_35_and_54_rh, result=83.4),
                                 above=79.0)),

            (82, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=89.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=86.7),
                                 above=82.5)),

            # 83 range
            (83, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=71.1),
                                between=Comparator(fn=between_68_and_87_rh, result=68.1),
                                above=65.5)),

            (83, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=73.2),
                                between=Comparator(fn=between_58_and_77_rh, result=70.0),
                                above=66.6)),

            (83, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=75.3),
                                between=Comparator(fn=between_48_and_67_rh, result=72.0),
                                above=67.7)),

            (83, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=78.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=75.6),
                                 above=71.3)),

            (83, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=82.4),
                                 between=Comparator(fn=between_38_and_57_rh, result=79.4),
                                 above=75.0)),

            (83, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=86.9),
                                 between=Comparator(fn=between_35_and_54_rh, result=84.0),
                                 above=79.5)),

            (83, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=89.6),
                                 between=Comparator(fn=between_33_and_52_rh, result=87.1),
                                 above=82.8)),

            # 84 range
            (84, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=72.1),
                                between=Comparator(fn=between_68_and_87_rh, result=68.9),
                                above=66.5)),

            (84, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=74.0),
                                between=Comparator(fn=between_58_and_77_rh, result=70.9),
                                above=67.6)),

            (84, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=76.1),
                                between=Comparator(fn=between_48_and_67_rh, result=78.0),
                                above=68.7)),

            (84, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=79.5),
                                 between=Comparator(fn=between_43_and_62_rh, result=76.5),
                                 above=72.1)),

            (84, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=83.1),
                                 between=Comparator(fn=between_38_and_57_rh, result=80.2),
                                 above=75.8)),

            (84, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=87.4),
                                 between=Comparator(fn=between_35_and_54_rh, result=84.6),
                                 above=80.1)),

            (84, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=89.9),
                                 between=Comparator(fn=between_33_and_52_rh, result=87.5),
                                 above=83.1)),

            # 85 range
            (85, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=73.1),
                                between=Comparator(fn=between_68_and_87_rh, result=69.8),
                                above=67.4)),

            (85, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=75.0),
                                between=Comparator(fn=between_58_and_77_rh, result=71.9),
                                above=68.6)),

            (85, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=76.9),
                                between=Comparator(fn=between_48_and_67_rh, result=74.0),
                                above=69.8)),

            (85, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=80.3),
                                 between=Comparator(fn=between_43_and_62_rh, result=77.4),
                                 above=73.1)),

            (85, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=83.8),
                                 between=Comparator(fn=between_38_and_57_rh, result=81.0),
                                 above=76.6)),

            (85, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=88.0),
                                 between=Comparator(fn=between_35_and_54_rh, result=85.3),
                                 above=80.7)),

            (85, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=90.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=87.9),
                                 above=83.4)),

            # 86 range
            (86, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=74.1),
                                between=Comparator(fn=between_68_and_87_rh, result=70.8),
                                above=68.4)),

            (86, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=75.9),
                                between=Comparator(fn=between_58_and_77_rh, result=72.8),
                                above=69.6)),

            (86, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=77.8),
                                between=Comparator(fn=between_48_and_67_rh, result=75.0),
                                above=70.8)),

            (86, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=81.1),
                                 between=Comparator(fn=between_43_and_62_rh, result=78.3),
                                 above=74.0)),

            (86, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=84.5),
                                 between=Comparator(fn=between_38_and_57_rh, result=81.9),
                                 above=77.3)),

            (86, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=88.5),
                                 between=Comparator(fn=between_35_and_54_rh, result=85.9),
                                 above=81.2)),

            (86, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=90.5),
                                 between=Comparator(fn=between_33_and_52_rh, result=88.2),
                                 above=83.7)),

            # 87 range
            (87, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=75.2),
                                between=Comparator(fn=between_68_and_87_rh, result=71.7),
                                above=69.4)),

            (87, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=76.9),
                                between=Comparator(fn=between_58_and_77_rh, result=73.9),
                                above=70.7)),

            (87, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=78.7),
                                between=Comparator(fn=between_48_and_67_rh, result=76.0),
                                above=71.9)),

            (87, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=81.9),
                                 between=Comparator(fn=between_43_and_62_rh, result=79.3),
                                 above=75.0)),

            (87, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=85.3),
                                 between=Comparator(fn=between_38_and_57_rh, result=82.7),
                                 above=78.2)),

            (87, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=89.0),
                                 between=Comparator(fn=between_35_and_54_rh, result=86.5),
                                 above=81.8)),

            (87, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=90.9),
                                 between=Comparator(fn=between_33_and_52_rh, result=88.6),
                                 above=84.0)),

            # 88 range
            (88, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=76.3),
                                between=Comparator(fn=between_68_and_87_rh, result=72.7),
                                above=70.5)),

            (88, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=77.9),
                                between=Comparator(fn=between_58_and_77_rh, result=74.9),
                                above=71.8)),

            (88, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=79.7),
                                between=Comparator(fn=between_48_and_67_rh, result=77.1),
                                above=73.1)),

            (88, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=82.8),
                                 between=Comparator(fn=between_43_and_62_rh, result=80.3),
                                 above=76.0)),

            (88, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=86.1),
                                 between=Comparator(fn=between_38_and_57_rh, result=83.6),
                                 above=79.0)),

            (88, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=89.6),
                                 between=Comparator(fn=between_35_and_54_rh, result=87.1),
                                 above=82.4)),

            (88, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=91.2),
                                 between=Comparator(fn=between_33_and_52_rh, result=88.9),
                                 above=84.3)),

            # 89 range
            (89, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=77.5),
                                between=Comparator(fn=between_68_and_87_rh, result=78.8),
                                above=71.6)),

            (89, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=79.0),
                                between=Comparator(fn=between_58_and_77_rh, result=75.9),
                                above=72.9)),

            (89, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=80.6),
                                between=Comparator(fn=between_48_and_67_rh, result=78.2),
                                above=74.3)),

            (89, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=83.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=81.3),
                                 above=77.0)),

            (89, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=86.9),
                                 between=Comparator(fn=between_38_and_57_rh, result=84.5),
                                 above=79.9)),

            (89, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=90.1),
                                 between=Comparator(fn=between_35_and_54_rh, result=87.7),
                                 above=82.9)),

            (89, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=91.5),
                                 between=Comparator(fn=between_33_and_52_rh, result=89.3),
                                 above=84.6)),

            # 90 range
            (90, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=78.7),
                                between=Comparator(fn=between_68_and_87_rh, result=74.8),
                                above=72.7)),

            (90, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=80.2),
                                between=Comparator(fn=between_58_and_77_rh, result=77.0),
                                above=74.1)),

            (90, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=81.7),
                                between=Comparator(fn=between_48_and_67_rh, result=79.3),
                                above=75.5)),

            (90, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=84.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=82.3),
                                 above=78.1)),

            (90, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=87.8),
                                 between=Comparator(fn=between_38_and_57_rh, result=85.5),
                                 above=80.8)),

            (90, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=90.6),
                                 between=Comparator(fn=between_35_and_54_rh, result=88.3),
                                 above=83.5)),

            (90, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=91.8),
                                 between=Comparator(fn=between_33_and_52_rh, result=89.7),
                                 above=84.9)),

            # 91 range
            (91, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=80.0),
                                between=Comparator(fn=between_68_and_87_rh, result=75.9),
                                above=73.8)),

            (91, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=81.4),
                                between=Comparator(fn=between_58_and_77_rh, result=78.2),
                                above=75.3)),

            (91, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=82.8),
                                between=Comparator(fn=between_48_and_67_rh, result=80.5),
                                above=76.8)),

            (91, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=85.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=83.4),
                                 above=79.2)),

            (91, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=88.7),
                                 between=Comparator(fn=between_38_and_57_rh, result=86.5),
                                 above=81.7)),

            (91, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=91.1),
                                 between=Comparator(fn=between_35_and_54_rh, result=88.9),
                                 above=84.0)),

            (91, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=92.1),
                                 between=Comparator(fn=between_33_and_52_rh, result=90.0),
                                 above=85.2)),

            # 92 range
            (92, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=81.3),
                                between=Comparator(fn=between_68_and_87_rh, result=77.1),
                                above=75.0)),

            (92, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=82.6),
                                between=Comparator(fn=between_58_and_77_rh, result=79.3),
                                above=76.5)),

            (92, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=83.9),
                                between=Comparator(fn=between_48_and_67_rh, result=81.7),
                                above=78.1)),

            (92, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=86.7),
                                 between=Comparator(fn=between_43_and_62_rh, result=84.5),
                                 above=80.3)),

            (92, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=89.7),
                                 between=Comparator(fn=between_38_and_57_rh, result=87.5),
                                 above=82.6)),

            (92, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=91.6),
                                 between=Comparator(fn=between_35_and_54_rh, result=89.4),
                                 above=84.6)),

            (92, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=92.4),
                                 between=Comparator(fn=between_33_and_52_rh, result=90.3),
                                 above=85.5)),

            # 93 range
            (93, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=82.7),
                                between=Comparator(fn=between_68_and_87_rh, result=78.3),
                                above=76.2)),

            (93, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=83.9),
                                between=Comparator(fn=between_58_and_77_rh, result=80.5),
                                above=77.8)),

            (93, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=85.1),
                                between=Comparator(fn=between_48_and_67_rh, result=82.9),
                                above=79.4)),

            (93, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=87.8),
                                 between=Comparator(fn=between_43_and_62_rh, result=85.7),
                                 above=81.5)),

            (93, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=90.6),
                                 between=Comparator(fn=between_38_and_57_rh, result=88.5),
                                 above=83.6)),

            (93, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=92.1),
                                 between=Comparator(fn=between_35_and_54_rh, result=90.0),
                                 above=85.1)),

            (93, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=92.7),
                                 between=Comparator(fn=between_33_and_52_rh, result=90.7),
                                 above=85.8)),

            # 94 range
            (94, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=84.1),
                                between=Comparator(fn=between_68_and_87_rh, result=79.5),
                                above=77.4)),

            (94, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=85.2),
                                between=Comparator(fn=between_58_and_77_rh, result=81.8),
                                above=79.1)),

            (94, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=86.3),
                                between=Comparator(fn=between_48_and_67_rh, result=84.1),
                                above=80.8)),

            (94, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=89.0),
                                 between=Comparator(fn=between_43_and_62_rh, result=86.8),
                                 above=82.7)),

            (94, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=91.7),
                                 between=Comparator(fn=between_38_and_57_rh, result=89.6),
                                 above=84.7)),

            (94, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=92.6),
                                 between=Comparator(fn=between_35_and_54_rh, result=90.6),
                                 above=85.6)),

            (94, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=93.0),
                                 between=Comparator(fn=between_33_and_52_rh, result=91.0),
                                 above=86.1)),

            # 95 range
            (95, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=85.7),
                                between=Comparator(fn=between_68_and_87_rh, result=80.8),
                                above=78.7)),

            (95, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=86.6),
                                between=Comparator(fn=between_58_and_77_rh, result=83.1),
                                above=80.5)),

            (95, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=87.7),
                                between=Comparator(fn=between_48_and_67_rh, result=85.4),
                                above=82.3)),

            (95, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=90.1),
                                 between=Comparator(fn=between_43_and_62_rh, result=88.0),
                                 above=84.0)),

            (95, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=92.7),
                                 between=Comparator(fn=between_38_and_57_rh, result=90.8),
                                 above=85.8)),

            (95, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=93.1),
                                 between=Comparator(fn=between_35_and_54_rh, result=91.2),
                                 above=86.2)),

            (95, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=93.3),
                                 between=Comparator(fn=between_33_and_52_rh, result=91.4),
                                 above=86.4)),

            # 96 range
            (96, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=87.2),
                                between=Comparator(fn=between_68_and_87_rh, result=82.2),
                                above=80.0)),

            (96, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=88.1),
                                between=Comparator(fn=between_58_and_77_rh, result=84.4),
                                above=81.9)),

            (96, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=89.0),
                                between=Comparator(fn=between_48_and_67_rh, result=86.6),
                                above=83.8)),

            (96, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=91.4),
                                 between=Comparator(fn=between_43_and_62_rh, result=89.2),
                                 above=85.3)),

            (96, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=93.8),
                                 between=Comparator(fn=between_38_and_57_rh, result=91.9),
                                 above=86.9)),

            (96, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=93.8),
                                 between=Comparator(fn=between_35_and_54_rh, result=91.9),
                                 above=86.9)),

            (96, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=93.8),
                                 between=Comparator(fn=between_33_and_52_rh, result=91.9),
                                 above=86.9)),

            # 97 range
            (97, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=88.8),
                                between=Comparator(fn=between_68_and_87_rh, result=83.6),
                                above=81.4)),

            (97, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=89.6),
                                between=Comparator(fn=between_58_and_77_rh, result=85.7),
                                above=83.3)),

            (97, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=90.4),
                                between=Comparator(fn=between_48_and_67_rh, result=87.9),
                                above=85.3)),

            (97, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=92.6),
                                 between=Comparator(fn=between_43_and_62_rh, result=90.5),
                                 above=86.7)),

            (97, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=94.9),
                                 between=Comparator(fn=between_38_and_57_rh, result=93.1),
                                 above=88.0)),

            (97, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=94.9),
                                 between=Comparator(fn=between_35_and_54_rh, result=93.1),
                                 above=88.0)),

            (97, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=94.9),
                                 between=Comparator(fn=between_33_and_52_rh, result=93.1),
                                 above=88.0)),

            # 98 range
            (98, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=90.4),
                                between=Comparator(fn=between_68_and_87_rh, result=85.0),
                                above=82.7)),

            (98, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=91.1),
                                between=Comparator(fn=between_58_and_77_rh, result=87.0),
                                above=84.8)),

            (98, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=91.9),
                                between=Comparator(fn=between_48_and_67_rh, result=89.1),
                                above=86.9)),

            (98, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=93.9),
                                 between=Comparator(fn=between_43_and_62_rh, result=91.7),
                                 above=88.1)),

            (98, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=96.0),
                                 between=Comparator(fn=between_38_and_57_rh, result=94.3),
                                 above=89.3)),

            (98, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=96.0),
                                 between=Comparator(fn=between_35_and_54_rh, result=94.3),
                                 above=89.3)),

            (98, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=96.0),
                                 between=Comparator(fn=between_33_and_52_rh, result=94.3),
                                 above=89.3)),

            # 99 range
            (99, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=91.9),
                                between=Comparator(fn=between_68_and_87_rh, result=86.5),
                                above=84.1)),

            (99, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=92.6),
                                between=Comparator(fn=between_58_and_77_rh, result=88.3),
                                above=86.2)),

            (99, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=93.3),
                                between=Comparator(fn=between_48_and_67_rh, result=90.2),
                                above=88.4)),

            (99, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=95.2),
                                 between=Comparator(fn=between_43_and_62_rh, result=92.8),
                                 above=89.5)),

            (99, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=97.1),
                                 between=Comparator(fn=between_38_and_57_rh, result=95.5),
                                 above=90.5)),

            (99, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=97.1),
                                 between=Comparator(fn=between_35_and_54_rh, result=95.5),
                                 above=90.5)),

            (99, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=97.1),
                                 between=Comparator(fn=between_33_and_52_rh, result=95.5),
                                 above=90.5)),

            # 100 range
            (100, 7, RHRangeFFMC(below=Comparator(fn=below_68_rh, result=93.2),
                                 between=Comparator(fn=between_68_and_87_rh, result=88.0),
                                 above=85.4)),

            (100, 8, RHRangeFFMC(below=Comparator(fn=below_58_rh, result=93.9),
                                 between=Comparator(fn=between_58_and_77_rh, result=89.5),
                                 above=87.6)),

            (100, 9, RHRangeFFMC(below=Comparator(fn=below_48_rh, result=94.6),
                                 between=Comparator(fn=between_48_and_67_rh, result=91.2),
                                 above=89.8)),

            (100, 10, RHRangeFFMC(below=Comparator(fn=below_43_rh, result=96.3),
                                  between=Comparator(fn=between_43_and_62_rh, result=93.8),
                                  above=90.8)),

            (100, 11, RHRangeFFMC(below=Comparator(fn=below_38_rh, result=97.9),
                                  between=Comparator(fn=between_38_and_57_rh, result=96.7),
                                  above=91.8)),

            (100, 12, RHRangeFFMC(below=Comparator(fn=below_35_dot_5_rh, result=97.9),
                                  between=Comparator(fn=between_35_and_54_rh, result=96.7),
                                  above=91.8)),

            (100, 13, RHRangeFFMC(below=Comparator(fn=below_33_rh, result=97.9),
                                  between=Comparator(fn=between_33_and_52_rh, result=96.7),
                                  above=91.8)),

        ]

        column_names = ['ffmc', 'hour', 'predicted_ffmc_range']
        self.yesterday_lookup = pd.DataFrame(data, columns=column_names)
        self.yesterday_lookup.set_index(['ffmc', 'hour'], inplace=True)

    def get(self, daily_ffmc: float, hour: int, rh: float) -> Optional[float]:
        if daily_ffmc < 50:
            return None

        # Round up and clamp to 100 if somehow over 100
        lookup_ffmc = min(100, math.ceil(daily_ffmc))

        if lookup_ffmc in range(0, 55):
            return self.yesterday_lookup.loc[(50, hour)]['predicted_ffmc_range'].for_rh(rh)
        elif lookup_ffmc in range(55, 65):
            return self.yesterday_lookup.loc[(60, hour)]['predicted_ffmc_range'].for_rh(rh)
        elif lookup_ffmc in range(65, 71):
            return self.yesterday_lookup.loc[(70, hour)]['predicted_ffmc_range'].for_rh(rh)
        elif lookup_ffmc in range(71, 72):
            return self.yesterday_lookup.loc[(72, hour)]['predicted_ffmc_range'].for_rh(rh)
        elif lookup_ffmc in range(73, 74):
            return self.yesterday_lookup.loc[(74, hour)]['predicted_ffmc_range'].for_rh(rh)
        else:
            return self.yesterday_lookup.loc[(lookup_ffmc, hour)]['predicted_ffmc_range'].for_rh(rh)
