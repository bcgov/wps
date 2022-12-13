import datetime

from tileserv.tools.tif_pusher import build_post_body_for_tiff


def test_get_post_body_forecast():
    run_date = datetime.date(2022, 9, 3)
    tif_object = {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220904.tif'}

    post_body = build_post_body_for_tiff(tif_object, run_date)
    assert post_body.get("key") == tif_object.get("Key")
    assert post_body.get("runtype") == "forecast"
    assert post_body.get("for_date") == "2022-09-04"
    assert post_body.get("run_date") == run_date.isoformat()


def test_get_post_body_actual():
    run_date = datetime.date(2022, 9, 3)
    tif_object = {'Key': 'sfms/uploads/actual/2022-09-03/hfi20220904.tif'}

    post_body = build_post_body_for_tiff(tif_object, run_date)
    assert post_body.get("key") == tif_object.get("Key")
    assert post_body.get("runtype") == "actual"
    assert post_body.get("for_date") == "2022-09-04"
    assert post_body.get("run_date") == run_date.isoformat()
