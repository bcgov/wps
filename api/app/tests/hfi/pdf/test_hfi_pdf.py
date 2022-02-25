""" Unit testing for hfi pdf logic """
from datetime import datetime, timedelta
from app.hfi.pdf.hfi_pdf import generate_pdf
from app.schemas.hfi_calc import HFIResultResponse, PlanningAreaResult

planning_area_result = PlanningAreaResult(planning_area_id=1,
                                          all_dailies_valid=True,
                                          highest_daily_intensity_group=2.0,
                                          mean_prep_level=2.0,
                                          daily_results=[])

result = HFIResultResponse(
    selected_prep_date=datetime.now(),
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=5),
    selected_station_code_ids=[1],
    planning_area_station_info=None,
    selected_fire_center_id=1,
    planning_area_hfi_results=[planning_area_result],
    planning_area_fire_starts={1: []})


def test_proto():
    """ TODO fill in """
    generate_pdf(result)
