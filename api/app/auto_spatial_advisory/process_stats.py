from app.auto_spatial_advisory.critical_hours import calculate_critical_hours
from app.auto_spatial_advisory.process_elevation_hfi import process_hfi_elevation
from app.auto_spatial_advisory.process_fuel_type_area import process_fuel_type_hfi_by_shape
from app.auto_spatial_advisory.process_high_hfi_area import process_high_hfi_area
from app.auto_spatial_advisory.process_hfi import RunType, process_hfi
from datetime import date, datetime


async def process_stats(run_type: RunType, run_datetime: datetime, run_date: date, for_date: date):
    await process_hfi(run_type, run_date, run_datetime, for_date)
    await process_hfi_elevation(run_type, run_date, run_datetime, for_date)
    await process_high_hfi_area(run_type, run_datetime, for_date)
    await process_fuel_type_hfi_by_shape(run_type, run_datetime, for_date)
    await calculate_critical_hours(run_type, run_datetime, for_date)
