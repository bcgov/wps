from argparse import Namespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wps_weather.db.models.wx_4panel_charts import ECCCModel
from wps_weather.eccc_grib_consumer import FileToDownload
from wps_weather.wx_4panel_charts.backfill import (
    build_downloads,
    download_inputs,
    run_backfill,
    source_url_for_key,
    validate_range,
)


def test_validate_range_uses_model_interval():
    assert validate_range(ECCCModel.GDPS, 0, 12) == 6
    assert validate_range(ECCCModel.RDPS, 0, 12) == 3


@pytest.mark.parametrize(
    ("model", "start_hour", "end_hour"),
    [
        (ECCCModel.GDPS, -6, 12),
        (ECCCModel.GDPS, 0, 241),
        (ECCCModel.GDPS, 0, 7),
        (ECCCModel.RDPS, 6, 3),
    ],
)
def test_validate_range_rejects_invalid_hours(model, start_hour, end_hour):
    with pytest.raises(ValueError):
        validate_range(model, start_hour, end_hour)


def test_source_url_for_key():
    key = "weather_models/20260929/model_gdps/15km/00/000/file.grib2"

    assert source_url_for_key(key, "20260929") == (
        "https://dd.weather.gc.ca/20260929/WXO-DD/model_gdps/15km/00/000/file.grib2"
    )


def test_build_downloads_uses_exact_chart_inputs():
    downloads = build_downloads(ECCCModel.GDPS, "20260929", "00", 0, 6, 6)

    assert len(downloads) == 17
    assert len({download.s3_key for download in downloads}) == 17
    assert all(download.url.endswith(download.s3_key.split("/", 2)[-1]) for download in downloads)


@pytest.mark.anyio
async def test_download_inputs_fails_when_any_download_fails(mocker):
    downloader = MagicMock()
    downloader.__aenter__ = AsyncMock(return_value=downloader)
    downloader.__aexit__ = AsyncMock(return_value=False)
    downloader.download_and_upload = AsyncMock(side_effect=[True, False])
    mocker.patch("wps_weather.wx_4panel_charts.backfill.GribDownloader", return_value=downloader)
    downloads = [
        FileToDownload("https://example.com/a", "a"),
        FileToDownload("https://example.com/b", "b"),
    ]

    with pytest.raises(RuntimeError, match="1 required"):
        await download_inputs(AsyncMock(), downloads, 2)


@pytest.mark.anyio
async def test_run_backfill_rejects_remote_object_store(mocker):
    mocker.patch(
        "wps_weather.wx_4panel_charts.backfill.get_endpoint_url",
        return_value="https://objects.example.com",
    )
    args = Namespace(
        model="GDPS",
        init_ymd="20260929",
        model_run="00",
        start_hour=0,
        end_hour=6,
        max_concurrent_downloads=1,
    )

    with pytest.raises(RuntimeError, match="loopback"):
        await run_backfill(args)
