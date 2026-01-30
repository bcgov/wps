"""Unit testing for VIIRS snow data processing"""

import builtins
import math
import os
import re
import types
from datetime import date, datetime, timedelta

import pytest
from pytest_mock import MockerFixture

from app.jobs import viirs_snow
from app.jobs.viirs_snow import (
    GLOBAL_ULX,
    GLOBAL_ULY,
    MODIS_SINUSOIDAL_PROJ4,
    TILE_SIZE_M,
    NoGranulesException,
    ViirsSnowJob,
    build_modis_sinu_wkt,
    compute_bounds_for_tile,
    read_tile_indices,
    translate_assign_sinu,
)

async def mock__get_bc_boundary_from_s3(self, temp_dir):
    return

# ---------- Helpers / fixtures ----------


@pytest.fixture
def mock_osr(monkeypatch):
    """
    Provide a mocked osgeo.osr.SpatialReference() that records calls and returns a fake WKT.
    """

    class FakeSpatialRef:
        def __init__(self):
            self.import_arg = None

        def ImportFromProj4(self, s):
            self.import_arg = s
            return 0  # success code

        def ExportToWkt(self):
            # Return a very simple (fake) WKT string for assertions
            return "FAKE_WKT_SINUSOIDAL"

    fake_osr_mod = types.SimpleNamespace(SpatialReference=FakeSpatialRef)

    # mock osgeo.osr import path
    fake_osgeo = types.SimpleNamespace(osr=fake_osr_mod)
    monkeypatch.setitem(builtins.__dict__, "osgeo", fake_osgeo)
    # Also patch name lookup inside module under test if it imported like: from osgeo import osr
    import app.jobs.viirs_snow as mut

    monkeypatch.setattr(mut, "osr", fake_osr_mod, raising=True)

    return fake_osr_mod


@pytest.fixture
def mock_gdal(monkeypatch):
    """
    Provide a mocked gdal with TranslateOptions and Translate.
    """

    class FakeTranslateOptions:
        def __init__(self, format=None, outputSRS=None, outputBounds=None):
            self.format = format
            self.outputSRS = outputSRS
            self.outputBounds = outputBounds

    class FakeDataset:
        def __init__(self):
            self.flushed = False

        def FlushCache(self):
            self.flushed = True

    calls = {
        "Translate_args": None,
        "Translate_opts": None,
    }

    def FakeTranslate(dst_tif, src_name, options=None):
        calls["Translate_args"] = (dst_tif, src_name)
        calls["Translate_opts"] = options
        # Return a dataset-like object to simulate success
        return FakeDataset()

    fake_gdal_mod = types.SimpleNamespace(
        TranslateOptions=FakeTranslateOptions,
        Translate=FakeTranslate,
        _calls=calls,
    )

    import app.jobs.viirs_snow as mut

    monkeypatch.setattr(mut, "gdal", fake_gdal_mod, raising=True)
    return fake_gdal_mod


# ---------- Tests: build_modis_sinu_wkt ----------


def test_build_modis_sinu_wkt_uses_proj4_and_returns_wkt(mock_osr):
    # Act
    wkt = build_modis_sinu_wkt()
    # Assert
    assert wkt == "FAKE_WKT_SINUSOIDAL"

    # Since SpatialReference is mocked, check it received the correct proj4
    sref = mock_osr.SpatialReference()
    sref.ImportFromProj4(MODIS_SINUSOIDAL_PROJ4)
    assert sref.import_arg == MODIS_SINUSOIDAL_PROJ4


# ---------- Tests: compute_bounds_for_tile ----------


@pytest.mark.parametrize(
    "h,v,width,height",
    [
        (0, 0, 1200, 1200),
        (10, 5, 2400, 2400),
        (35, 17, 480, 960),  # non-square pixels test (still uses px=py from TILE/pixels)
    ],
)
def test_compute_bounds_for_tile_basic(h, v, width, height):
    ulx, uly, lrx, lry, px, py = compute_bounds_for_tile(h, v, width, height)

    # Pixel size is tile-size divided by pixels
    assert math.isclose(px, TILE_SIZE_M / float(width), rel_tol=0, abs_tol=1e-12)
    assert math.isclose(py, TILE_SIZE_M / float(height), rel_tol=0, abs_tol=1e-12)

    # The UL corner is derived from global UL + offsets by h, v
    expected_ulx = GLOBAL_ULX + h * TILE_SIZE_M
    expected_uly = GLOBAL_ULY - v * TILE_SIZE_M
    assert math.isclose(ulx, expected_ulx, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(uly, expected_uly, rel_tol=0, abs_tol=1e-9)

    # lrx/lry should shift by width*px and height*py respectively
    assert math.isclose(lrx, ulx + width * px, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(lry, uly - height * py, rel_tol=0, abs_tol=1e-9)


def test_compute_bounds_for_tile_edge_case_1px():
    h, v, width, height = 1, 2, 1, 1
    ulx, uly, lrx, lry, px, py = compute_bounds_for_tile(h, v, width, height)

    assert math.isclose(px, TILE_SIZE_M, abs_tol=1e-9)
    assert math.isclose(py, TILE_SIZE_M, abs_tol=1e-9)
    assert math.isclose(ulx, GLOBAL_ULX + 1 * TILE_SIZE_M, abs_tol=1e-9)
    assert math.isclose(uly, GLOBAL_ULY - 2 * TILE_SIZE_M, abs_tol=1e-9)
    assert math.isclose(lrx, ulx + TILE_SIZE_M, abs_tol=1e-9)
    assert math.isclose(lry, uly - TILE_SIZE_M, abs_tol=1e-9)


# ---------- Tests: read_tile_indices ----------


def test_read_tile_indices_from_metadata_lowercase_keys():
    meta = {"HorizontalTileNumber": "12", "VerticalTileNumber": "07"}
    h, v = read_tile_indices(meta, "anything.h12v07.hd5")
    assert h == 12 and v == 7


def test_read_tile_indices_from_metadata_uppercase_keys():
    meta = {"HORIZONTALTILENUMBER": 3, "VERTICALTILENUMBER": 9}
    h, v = read_tile_indices(meta, "whatever.h00v00.hd5")
    assert h == 3 and v == 9


def test_read_tile_indices_from_filename_only():
    meta = {}
    h, v = read_tile_indices(meta, "VNP10A1F.A2024013.h12v34.001.hd5")
    assert h == 12 and v == 34


def test_read_tile_indices_mixed_missing_one_from_meta_and_filename_fills_other():
    meta = {"HORIZONTALTILENUMBER": "05"}
    h, v = read_tile_indices(meta, "something_h05v18_more.hd5")
    assert h == 5 and v == 18


def test_read_tile_indices_raises_if_not_found():
    meta = {"something": "else"}
    with pytest.raises(RuntimeError, match="Could not determine tile indices"):
        read_tile_indices(meta, "no_tile_here.dat")


def test_read_tile_indices_ignores_bad_meta_types():
    meta = {"HorizontalTileNumber": "not_an_int", "VerticalTileNumber": "also_bad"}
    h, v = read_tile_indices(meta, "prefix_h02v03_suffix.tif")
    assert (h, v) == (2, 3)


# ---------- Tests: translate_assign_sinu ----------


def test_translate_assign_sinu_happy_path(mock_gdal, mock_osr):
    sinu_wkt = build_modis_sinu_wkt()  # returns FAKE_WKT_SINUSOIDAL via mock
    ulx, uly, lrx, lry = -100.0, 50.0, -90.0, 40.0

    translate_assign_sinu(
        src_name="in.hdf",
        dst_tif="out.tif",
        ulx=ulx,
        uly=uly,
        lrx=lrx,
        lry=lry,
        sinu_wkt=sinu_wkt,
    )

    # Validate TranslateOptions and Translate call
    opts = mock_gdal._calls["Translate_opts"]
    assert opts is not None
    assert opts.format == "GTiff"
    assert opts.outputSRS == "FAKE_WKT_SINUSOIDAL"
    assert opts.outputBounds == [ulx, uly, lrx, lry]
    assert mock_gdal._calls["Translate_args"] == ("out.tif", "in.hdf")


def test_translate_assign_sinu_raises_when_translate_returns_none(monkeypatch, mock_osr):
    # Build a gdal mock that returns None for Translate to simulate failure
    class FakeTranslateOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    def FakeTranslate(*args, **kwargs):
        return None

    import app.jobs.viirs_snow as mut

    fake_gdal_mod = types.SimpleNamespace(
        TranslateOptions=FakeTranslateOptions,
        Translate=FakeTranslate,
    )
    monkeypatch.setattr(mut, "gdal", fake_gdal_mod, raising=True)

    sinu_wkt = build_modis_sinu_wkt()
    with pytest.raises(RuntimeError, match="gdal.Translate failed"):
        translate_assign_sinu("in.hdf", "out.tif", -1, 1, 2, -2, sinu_wkt)


def test_viirs_snow_job_fail(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    async def mock__get_last_processed_date(self):
        raise OSError("Error")

    monkeypatch.setattr(ViirsSnowJob, "_get_last_processed_date", mock__get_last_processed_date)
    rocket_chat_spy = mocker.spy(viirs_snow, "send_rocketchat_notification")
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_viirs_snow_job_exits_without_error_when_no_work_required(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
):
    """Test that viirs_snow_job exits without error when no data needs to be processed."""

    async def mock__get_last_processed_date(self, for_date: datetime):
        return date.today() - timedelta(days=1)

    monkeypatch.setattr(ViirsSnowJob, "_get_last_processed_date", mock__get_last_processed_date)
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK


def test_viirs_snow_job_exits_cleanly_when_no_viirs_data(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
):
    """Test that viirs_snow_job exits cleanly when attempt to download data that doesn't exist
    throws a HTTPError with status code of 501.
    """

    async def mock__get_last_processed_date(self, for_date: datetime):
        return date.today() - timedelta(days=2)

    def mock__download_viirs_granules_by_date(self, for_date: date, path: str):
        raise NoGranulesException("No granules available.")

    monkeypatch.setattr(ViirsSnowJob, "_get_last_processed_date", mock__get_last_processed_date)
    monkeypatch.setattr(ViirsSnowJob, "_get_bc_boundary_from_s3", mock__get_bc_boundary_from_s3)
    monkeypatch.setattr(
        ViirsSnowJob, "_download_viirs_granules_by_date", mock__download_viirs_granules_by_date
    )
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK


def test_viirs_snow_job_fails_on_earthdata_access_auth_failure(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
):
    """
    Test that when authentication with the NSIDC fails a message is sent to rocket-chat and our exit code is 1.
    """

    async def mock__get_last_processed_date(self):
        return date.today() - timedelta(days=2)

    def mock__download_viirs_granules_by_date(self, for_date: date, path: str):
        raise AssertionError()

    monkeypatch.setattr(ViirsSnowJob, "_get_last_processed_date", mock__get_last_processed_date)
    monkeypatch.setattr(ViirsSnowJob, "_get_bc_boundary_from_s3", mock__get_bc_boundary_from_s3)
    monkeypatch.setattr(
        ViirsSnowJob, "_download_viirs_granules_by_date", mock__download_viirs_granules_by_date
    )
    # mock sys.argv with a random path, otherwise argparser will pickup the sys.argv args from pytest
    mocker.patch("sys.argv", ["/test"])

    rocket_chat_spy = mocker.spy(viirs_snow, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        viirs_snow.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1
