""" This module contains pydandict schemas the HFI Calculator.
"""
from typing import List, Dict, Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.schemas.shared import FuelType


class StationDaily(BaseModel):
    """ Station Daily metrics for HFI daily table """
    code: Optional[int] = None
    status: Optional[str] = None
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    grass_cure_percentage: Optional[float] = None
    precipitation: Optional[float] = None
    ffmc: Optional[float] = None
    dmc: Optional[float] = None
    dc: Optional[float] = None
    isi: Optional[float] = None
    bui: Optional[float] = None
    fwi: Optional[float] = None
    danger_class: Optional[int] = None
    observation_valid: Optional[bool] = None
    observation_valid_comment: Optional[str] = None
    rate_of_spread: Optional[float] = None
    hfi: Optional[float] = None
    intensity_group: Optional[int] = None
    sixty_minute_fire_size: Optional[float] = None
    fire_type: Optional[str] = None
    error: Optional[bool] = False
    error_message: Optional[str] = None
    date: Optional[datetime] = None
    last_updated: Optional[datetime] = None


required_daily_fields = ['temperature',
                         'relative_humidity',
                         'wind_speed',
                         'wind_direction',
                         'precipitation',
                         'intensity_group']


class StationDailyResponse(BaseModel):
    """ Response that includes list of station daily data."""
    dailies: List[StationDaily]


class ValidatedStationDaily(BaseModel):
    """
    Station daily with validity flag
    """
    daily: StationDaily
    valid: bool


class FireStartRange(BaseModel):
    """
    User facing label, value and lookup table of fire starts to prep level
    """
    label: str
    id: int


class DailyResult(BaseModel):
    """
    Prep level, MIG, fire starts and station daily results for a day in a prep week
    """
    date: date
    dailies: List[ValidatedStationDaily]
    fire_starts: FireStartRange
    mean_intensity_group: Optional[float]
    prep_level: Optional[float]


class PlanningAreaResult(BaseModel):
    """
    Mean prep level / max intensity group,
    dailies and validity status of station dailies in a planning area
    """
    planning_area_id: int
    all_dailies_valid: bool
    highest_daily_intensity_group: Optional[float]
    mean_prep_level: Optional[float]
    daily_results: List[DailyResult]


class WeatherStationProperties(BaseModel):
    """ HFI-relevant weather station properties """
    name: str
    elevation: int
    fuel_type: FuelType
    wfwx_station_uuid: str


class WeatherStation(BaseModel):
    """ A fire weather station has a code, planning area, and other properties specific to the station. """
    code: int
    station_props: WeatherStationProperties
    order_of_appearance_in_planning_area_list: Optional[int]


class PlanningArea(BaseModel):
    """ A planning area (a.k.a. zone) is a small group of stations selected to represent a particular
    zone within a fire centre. """
    id: int
    name: str
    order_of_appearance_in_list: Optional[int]
    stations: List[WeatherStation]


class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    id: int
    name: str
    planning_areas: List[PlanningArea]


class HFIWeatherStationsResponse(BaseModel):
    """ A list of WeatherStations, where each WeatherStation has nested within it all relevant information
    specific to BCWS planning operations. """
    fire_centres: List[FireCentre]


class StationInfo(BaseModel):
    """ Information about a station, including its code, name, and elevation. """
    station_code: int
    selected: bool
    # fuel_type_id matches to table fuel_types.id
    fuel_type_id: int


class DateRange(BaseModel):
    """ A Pythonic implementation of the DateRange construct we use on the front-end in Typescript. """
    start_date: Optional[date]
    end_date: Optional[date]

    def days_in_range(self) -> Optional[int]:
        """ Calculate the number of days (inclusive) in the date range. """
        if self.start_date and self.end_date:
            # num prep days is inclusive, so we need to add 1
            return (self.end_date - self.start_date).days + 1
        return None


class HFIResultRequest(BaseModel):
    """
    Request that contains inputs necessary for calculating HFI.

    If a component on the front end needs a timestamp, then convert "2022-01-01" to a datetime at noon PST.
    Vice versa, if a component is working in terms of a timestamp, then convert from that timestamp to
    a ISO date string in PST, then grab the YYYY-MM-DD part.
    The PST part is critical, so that the date doesn't change due to timezone switches.
    """
    selected_fire_center_id: int
    date_range: DateRange
    # Each planning area has a list of stations
    planning_area_station_info: Dict[int, List[StationInfo]]
    # Mapping from planning area id to a map of FireStartRanges.
    planning_area_fire_starts: Dict[int, List[FireStartRange]]


class HFIResultResponse(BaseModel):
    """
    Response that contains daily data, num prep days, selected station codes,
    selected fire centre, fire starts, HFI results.
    """
    date_range: DateRange
    planning_area_station_info: Dict[int, List[StationInfo]]
    selected_fire_center_id: int
    planning_area_hfi_results: List[PlanningAreaResult]
    # Each planning area may have it's own custom fire starts information - so we include it in
    # the response for convenience. (We could require the front end to make a seperate call to load
    # fire start ranges for a fire centre, instead of sending it up on every response.)
    fire_start_ranges: List[FireStartRange]


class StationPDFData(StationDaily, WeatherStation):
    """ All the details we have about stations """


class PrepTablePlanningAreaPDFData(BaseModel):
    """ Data needed for prep cycle PDF sheet """
    planning_area_name: str
    order: int
    highest_daily_intensity_group: Optional[float]
    mean_prep_level: Optional[float]
    mean_intensity_groups: List[Optional[float]]
    fire_starts_labels: List[str]
    prep_levels: List[Optional[int]]
    # Station dailies grouped by station code containing the dailies for each day in the prep cycle
    dailies: Dict[int, List[StationPDFData]]


class DailyTablePlanningAreaPDFData(BaseModel):
    """ Data needed for daily PDF sheet """
    planning_area_name: str
    mean_intensity_group: Optional[float]
    prep_level: Optional[float]
    fire_starts: str
    date: str
    # Every station daily in the above planning area for the specific day
    dailies: List[StationPDFData]
