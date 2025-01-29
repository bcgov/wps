from datetime import date
import json
from typing import Dict
import asyncio

from pydantic import BaseModel
from app.auto_spatial_advisory.critical_hours import CriticalHoursInputOutput, calculate_critical_hours_by_fuel_type
from app.utils.s3 import get_client, object_exists_v2


class CriticalHoursIOByZone(BaseModel):
    critical_hours_by_zone: Dict[int, CriticalHoursInputOutput]


## Fill this info in manually for the zone/run you want to debug
ZONE_NUMBER = 85
for_date = date(2024, 8, 14)
# SELECT * FROM run_parameters rp WHERE for_date = 'YYY-MM-DD'
run_parameters_id = 3517


async def get_json_from_s3():
    async with get_client() as (client, bucket):
        key = f"critical_hours/{for_date.isoformat()}/{run_parameters_id}_critical_hours.json"
        exists = await object_exists_v2(key)
        if exists:
            res = await client.get_object(Bucket=bucket, Key=key)
            body = await res["Body"].read()
            json_content = json.loads(body.decode("utf-8"))
            critical_hours_io = CriticalHoursIOByZone(critical_hours_by_zone=json_content)
            return critical_hours_io.critical_hours_by_zone
        else:
            print("Critical hours json not found")


async def calculate_critical_hours():
    critical_hours_io = await get_json_from_s3()
    if critical_hours_io:
        zone_critical_hours = critical_hours_io[ZONE_NUMBER]

        wfwx_stations = zone_critical_hours.wfwx_stations
        fuel_types_by_area = zone_critical_hours.fuel_types_by_area
        critical_hours_inputs = zone_critical_hours.critical_hours_inputs

        # this object contain the previously calculated and saved results
        # critical_hours_by_zone_and_fuel_type = zone_critical_hours.critical_hours_by_zone_and_fuel_type
        # previous_zone_results = critical_hours_by_zone_and_fuel_type[ZONE_NUMBER]

        # start debugging
        calculate_critical_hours_by_fuel_type(wfwx_stations, critical_hours_inputs, fuel_types_by_area, for_date)


if __name__ == "__main__":
    asyncio.run(calculate_critical_hours())
