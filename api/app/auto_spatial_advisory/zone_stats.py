"""
Functions for computing fuel type stats
"""
import logging
from datetime import date
from typing import List, Optional
from wps_shared.db.models.auto_spatial_advisory import (
    SFMSFuelType as DBSFMSFuelType,
    AdvisoryHFIWindSpeed
)
from wps_shared.schemas.fba import (
    AdvisoryCriticalHours,
    ClassifiedHfiThresholdFuelTypeArea,
    HfiThreshold,
    SFMSFuelType,
    AdvisoryMinWindStats
)

logger = logging.getLogger(__name__)


"""
    <!-- Percent Curing default values from June 2021 -->
    <!-- November 1 to July 15 - 60% -->
    <!-- July 16 to July 30 - 70% -->
    <!-- July 31 to August 15 - 80% -->
    <!-- August 16 - October 31 (end of season) - 90% -->
"""
def get_optional_percent_curing(grass_curing_date: date, sfms_fuel_type: DBSFMSFuelType):
    # 12 is the sfms fuel id for grass types
    if sfms_fuel_type is None or sfms_fuel_type.fuel_type_id != 12:
        return None
    
    if grass_curing_date >= date(grass_curing_date.year, 11, 1) and grass_curing_date <= date(grass_curing_date.year, 12, 31):
        return 60
    if grass_curing_date >= date(grass_curing_date.year, 1, 1) and grass_curing_date <= date(grass_curing_date.year, 7, 15):
        return 60
    if grass_curing_date >= date(grass_curing_date.year, 7, 16) and grass_curing_date <= date(grass_curing_date.year, 7, 30):
        return 70
    if grass_curing_date >= date(grass_curing_date.year, 7, 31) and grass_curing_date <= date(grass_curing_date.year, 8, 15):
        return 80
    if grass_curing_date >= date(grass_curing_date.year, 8, 16) and grass_curing_date <= date(grass_curing_date.year, 10, 31):
        return 90
    
    return None


def get_fuel_type_area_stats(
    grass_curing_date: date,
    sfms_fuel_types: List[(DBSFMSFuelType)],
    hfi_threshold: HfiThreshold,
    percent_conifer: Optional[int],
    critical_hour_start: Optional[float],
    critical_hour_end: Optional[float],
    fuel_type_id: int,
    area: float,
    fuel_area: float,
):
    fuel_type_obj: DBSFMSFuelType = next(
        (ft for ft in sfms_fuel_types if ft.id == fuel_type_id), None
    )
    percent_curing = get_optional_percent_curing(grass_curing_date, fuel_type_obj)
    fuel_type_code_details = fuel_type_obj.fuel_type_code + (f" (≥{percent_conifer} PC)" if percent_conifer is not None else "")
    return ClassifiedHfiThresholdFuelTypeArea(
        fuel_type=SFMSFuelType(fuel_type_id=fuel_type_obj.fuel_type_id, fuel_type_code=fuel_type_code_details, description=fuel_type_obj.description),
        threshold=hfi_threshold,
        critical_hours=AdvisoryCriticalHours(start_time=critical_hour_start, end_time=critical_hour_end),
        area=area,
        fuel_area=fuel_area,
        percent_curing=percent_curing)


def get_zone_wind_stats_for_source_id(zone_wind_stats: List[AdvisoryHFIWindSpeed], hfi_thresholds_by_id: dict[int, HfiThreshold]) -> List[AdvisoryMinWindStats]:
    """ Marshall AdvisoryHFIWindSpeed data model objects into AdvisoryMinWindStats API model objects.

    :param zone_wind_stats: advisory hfi wind speeds for a zone
    :param hfi_thresholds_by_id: hfi thresholds keyed by their ids
    :return: List of AdvisoryMinWindStats objects
    """
    all_zone_wind_stats = []
    for zone_wind_stats in zone_wind_stats:
            hfi_threshold = hfi_thresholds_by_id.get(zone_wind_stats.threshold)
            if hfi_threshold is None:
                logger.error(f"No hfi threshold for id: ${zone_wind_stats.threshold}")
                continue
            all_zone_wind_stats.append(AdvisoryMinWindStats(threshold=hfi_threshold, min_wind_speed=zone_wind_stats.min_wind_speed if zone_wind_stats else None))

    return all_zone_wind_stats