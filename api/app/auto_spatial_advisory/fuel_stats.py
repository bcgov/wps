"""
Functions for computing fuel type stats
"""
from datetime import date
from typing import List, Optional
from wps_shared.db.models.auto_spatial_advisory import HfiClassificationThreshold, SFMSFuelType as DBSFMSFuelType
from wps_shared.schemas.fba import (
    AdvisoryCriticalHours,
    ClassifiedHfiThresholdFuelTypeArea,
    HfiThreshold,
    SFMSFuelType
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
    
    # we can straddle a prev calendar year and the next calendar year with this date range case, nov 1, 2024 and jul 15, 2025
    if grass_curing_date.month == 11 or grass_curing_date.month == 12:
        if grass_curing_date >= date(grass_curing_date.year, 11, 1) and grass_curing_date <= date(grass_curing_date.year + 1, 7, 15):
            return 60
    elif grass_curing_date <= date(grass_curing_date.year, 7, 15):
            return 60
    if grass_curing_date >= date(grass_curing_date.year, 7, 16) and grass_curing_date <= date(grass_curing_date.year, 7, 30):
        return 70
    if grass_curing_date >= date(grass_curing_date.year, 7, 31) and grass_curing_date <= date(grass_curing_date.year, 8, 15):
        return 80
    if grass_curing_date >= date(grass_curing_date.year, 8, 16) and grass_curing_date <= date(grass_curing_date.year, 10, 31):
        return 90
    
    return None

def get_fuel_type_area_stats(grass_curing_date: date,
                             sfms_fuel_types: List[(DBSFMSFuelType)], 
                             thresholds: List[HfiClassificationThreshold], 
                             critical_hour_start: Optional[float],
                             critical_hour_end: Optional[float],
                             fuel_type_id: int,
                             threshold_id: int,
                             area: float,
                             fuel_area: float):
    # area is stored in square metres in DB. For user convenience, convert to hectares
    # 1 ha = 10,000 sq.m.
    area = area / 10000
    fuel_area = fuel_area / 10000
    fuel_type_obj: DBSFMSFuelType = next((ft[0] for ft in sfms_fuel_types if ft[0].id == fuel_type_id), None)
    percent_curing = get_optional_percent_curing(grass_curing_date, fuel_type_obj)
    threshold_obj: HfiClassificationThreshold = next((th for th in thresholds if th.id == threshold_id), None)
    return ClassifiedHfiThresholdFuelTypeArea(
        fuel_type=SFMSFuelType(fuel_type_id=fuel_type_obj.fuel_type_id, fuel_type_code=fuel_type_obj.fuel_type_code, description=fuel_type_obj.description),
        threshold=HfiThreshold(id=threshold_obj.id, name=threshold_obj.name, description=threshold_obj.description),
        critical_hours=AdvisoryCriticalHours(start_time=critical_hour_start, end_time=critical_hour_end),
        area=area,
        fuel_area=fuel_area,
        percent_curing=percent_curing)