"""
Run the consumer processing logic locally
Expects

   'OBJECT_STORE_SECRET'
   'OBJECT_STORE_USER_ID'
   'OBJECT_STORE_SERVER'

to be set
"""

import sys
import asyncio
from datetime import date
from .. import process_hfi
from .. import process_elevation_hfi
from .. import process_fuel_type_area
from .. import process_high_hfi_area
from .. import critical_hours

if __name__ == "__main__":
    asyncio.run(process_hfi.process_hfi(process_hfi.RunType.ACTUAL, date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3])))
    asyncio.run(
        process_elevation_hfi.process_hfi_elevation(process_hfi.RunType.ACTUAL, date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3]))
    )
    asyncio.run(process_high_hfi_area.process_high_hfi_area(process_hfi.RunType.ACTUAL, date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3])))
    asyncio.run(process_fuel_type_area.process_fuel_type_hfi_by_shape(process_hfi.RunType.ACTUAL, date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3])))
    asyncio.run(critical_hours.calculate_critical_hours(process_hfi.RunType.ACTUAL, date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3])))
