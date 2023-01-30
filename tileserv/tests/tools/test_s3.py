from dateutil.tz import tzutc
import datetime

from tileserv.tools.s3 import get_hfi_objects

utc = tzutc()

test_objects = [
    {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220903.tif', 'LastModified': datetime.datetime(
        2022, 9, 7, 18, 6, 26, 556000, tzinfo=utc)},
    {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220904.tif', 'LastModified': datetime.datetime(
        2022, 9, 7, 18, 6, 26, 695000, tzinfo=utc)},
    {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220905.tif', 'LastModified': datetime.datetime(
        2022, 9, 7, 18, 6, 27, 33000, tzinfo=utc)},
    {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220906.tif', 'LastModified': datetime.datetime(
        2022, 9, 7, 18, 6, 27, 513000, tzinfo=utc)},
]


def test_get_objects_only_hfi():
    objects = [
        {'Key': 'sfms/uploads/forecast/2022-09-03/bui20220903.tif', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 556000, tzinfo=utc)},
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220904.tif', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 695000, tzinfo=utc)}
    ]
    res = get_hfi_objects(objects)
    assert res[0] == objects[1]


def test_get_objects_all_hfi():
    objects = [
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220903.tif', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 556000, tzinfo=utc)},
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220904.tif', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 695000, tzinfo=utc)}
    ]
    res = get_hfi_objects(objects)
    assert res == objects


def test_get_objects_tif_or_tiff():
    objects = [
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220903.tiff', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 556000, tzinfo=utc)},
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220904.tif', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 695000, tzinfo=utc)}
    ]
    res = get_hfi_objects(objects)
    assert res == objects


def test_get_objects_ignore_non_tiff():
    objects = [
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220903.docx', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 556000, tzinfo=utc)},
        {'Key': 'sfms/uploads/forecast/2022-09-03/hfi20220904.docx', 'LastModified': datetime.datetime(
            2022, 9, 7, 18, 6, 26, 695000, tzinfo=utc)}
    ]
    res = get_hfi_objects(objects)
    assert res == []
