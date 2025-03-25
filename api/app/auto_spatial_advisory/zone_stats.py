"""
Functions for computing fuel type stats
"""
from datetime import date
from typing import List, Optional
from wps_shared.db.models.auto_spatial_advisory import (
    HfiClassificationThreshold, 
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

def get_hfi_threshold(threshold_id: int, thresholds: List[HfiClassificationThreshold]) -> HfiThreshold:
    threshold_obj: HfiClassificationThreshold = next((th for th in thresholds if th.id == threshold_id), None)
    return HfiThreshold(id=threshold_obj.id, name=threshold_obj.name, description=threshold_obj.description)


def get_fuel_type_area_stats(grass_curing_date: date,
                             sfms_fuel_types: List[(DBSFMSFuelType)],
                             hfi_threshold: HfiThreshold,
                             percent_conifer: Optional[int],
                             critical_hour_start: Optional[float],
                             critical_hour_end: Optional[float],
                             fuel_type_id: int,
                             area: float,
                             fuel_area: float):
    # area is stored in square metres in DB. For user convenience, convert to hectares
    # 1 ha = 10,000 sq.m.
    area = area / 10000
    fuel_area = fuel_area / 10000
    fuel_type_obj: DBSFMSFuelType = next((ft[0] for ft in sfms_fuel_types if ft[0].id == fuel_type_id), None)
    percent_curing = get_optional_percent_curing(grass_curing_date, fuel_type_obj)
    fuel_type_code_details = fuel_type_obj.fuel_type_code + (f" (≥{percent_conifer} PC)" if percent_conifer is not None else "")
    return ClassifiedHfiThresholdFuelTypeArea(
        fuel_type=SFMSFuelType(fuel_type_id=fuel_type_obj.fuel_type_id, fuel_type_code=fuel_type_code_details, description=fuel_type_obj.description),
        threshold=hfi_threshold,
        critical_hours=AdvisoryCriticalHours(start_time=critical_hour_start, end_time=critical_hour_end),
        area=area,
        fuel_area=fuel_area,
        percent_curing=percent_curing)


def get_zone_wind_stats(zone_id: str, zone_wind_stats: dict[int, List[AdvisoryHFIWindSpeed]], hfi_threshold: HfiThreshold) -> AdvisoryMinWindStats:
    """Marshalls hfi and min wind speeds into AdvisoryMinWindStats

    Args:
        zone_id: zone id stats apply to
        zone_wind_stats: all wind stats keyed by zone id
        hfi_threshold: hfi threshold associated with stats

    Returns:
        AdvisoryMinWindStats: minimum wind stats for this hfi threshold for this zone
    """
    all_zone_wind_stats = zone_wind_stats.get(int(zone_id), [])
    wind_stats_for_threshold = next((stat for stat in all_zone_wind_stats if stat.threshold == hfi_threshold.id), None)
    return AdvisoryMinWindStats(threshold=hfi_threshold, min_wind_speed=wind_stats_for_threshold.min_wind_speed if wind_stats_for_threshold else None)