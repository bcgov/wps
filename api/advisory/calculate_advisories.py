""" Proof of concept - generating advisories """
import asyncio
from datetime import date
from advisory.db.database.tileserver import get_tileserver_write_session_scope
from advisory.db.crud import get_hfi_area_percentages
from app.db.crud.fba_advisory import save_advisory
from app.db.models.advisory import FireZoneAdvisory


async def generate_advisories(today: date):
    # NOTE! This was a quick hack to get something to work locally - and is not the way
    # we should approach it. I think we need to generate simplified zone polygons with
    # layer properties that contain percentages etc. etc.
    with get_tileserver_write_session_scope() as tileserver_session:
        rows = await get_hfi_area_percentages(tileserver_session, today)

        # Fetch rows.
        for row in rows:
            zone_area = row.zone_area
            hfi_area = row.hfi_area
            print(f'{row.mof_fire_zone_name}:{hfi_area}/{zone_area}={hfi_area/zone_area*100}%')

            advisory = FireZoneAdvisory(
                for_date=today.isoformat(),
                mof_fire_zone_id=row.mof_fire_zone_id,
                elevated_hfi_area=row.hfi_area,
                elevated_hfi_percentage=hfi_area / zone_area * 100)
            await save_advisory(tileserver_session, advisory)


if __name__ == '__main__':
    asyncio.run(generate_advisories(date.fromisoformat('2022-08-06')))
