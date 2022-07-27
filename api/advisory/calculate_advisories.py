from advisory.db.database.tileserver import get_tileserver_session_scope
from advisory.db.crud import get_hfi_area_percentages
from app.db.database import get_write_session_scope
from app.db.crud.fba_advisory import save_advisory
from app.db.models.advisory import FireZoneAdvisory


def generate_advisories():
    with get_tileserver_session_scope() as tileserver_session:
        rows = get_hfi_area_percentages(tileserver_session)

        # Fetch rows.
        for row in rows:
            zone_area = row.zone_area
            hfi_area = row.hfi_area
            print(f'{row.mof_fire_zone_name}:{hfi_area}/{zone_area}={hfi_area/zone_area*100}%')

            advisory = FireZoneAdvisory(
                mof_fire_zone_id=row.mof_fire_zone_id,
                elevated_hfi_area=row.hfi_area,
                elevated_hfi_percentage=hfi_area / zone_area * 100)
            with get_write_session_scope() as wps_write_session:
                save_advisory(wps_write_session, advisory)


if __name__ == '__main__':
    generate_advisories()
