from datetime import date

from wps_shared.utils.object_store_keys import object_store_key


def get_critical_hours_key(for_date: date, run_parameters_id: int) -> str:
    return object_store_key(
        f"critical_hours/{for_date.isoformat()}/{run_parameters_id}_critical_hours.json"
    )
