from app.db.database import get_hfi_read_session_scope
from app.db.crud.fba_advisory import get_hfi_area_percentages, save_advisory
from app.db.external_models.fba_advisory import FireZoneAdvisory


def generate_advisories():
    with get_hfi_read_session_scope() as session:
        rows = get_hfi_area_percentages(session)

        # Fetch rows.
        for row in rows:
            zone_area = row.zone_area
            hfi_area = row.hfi_area
            print(f'{row.mof_fire_zone_name}:{hfi_area}/{zone_area}={hfi_area/zone_area*100}%')

            advisory = FireZoneAdvisory(fire_zone_id=row.id, elevated_hfi_area=row.hfi_area)
            save_advisory(session, advisory)


if __name__ == '__main__':
    generate_advisories()
