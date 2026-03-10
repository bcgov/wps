from unittest.mock import AsyncMock, MagicMock

import pytest

from wps_sfms.publish import publish_dataset
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.tests.geospatial.dataset_common import create_test_dataset


@pytest.mark.anyio
async def test_publish_dataset_uploads_raster_and_generates_cog_by_default(mocker):
    output_key = "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
    expected_cog_key = SFMSNGRasterAddresser().get_cog_key(output_key)
    generate_cog_spy = mocker.patch(
        "wps_sfms.publish.generate_web_optimized_cog",
        return_value=expected_cog_key,
    )

    mock_s3_client = MagicMock()
    mock_s3_client.put_object = AsyncMock()

    gdal_ds = create_test_dataset(
        "temperature_20240704.tif",
        1,
        1,
        (-1.0, 1.0, -1.0, 1.0),
        4326,
        fill_value=12.5,
        no_data_value=-9999.0,
    )

    with WPSDataset(ds_path=None, ds=gdal_ds) as dataset:
        published = await publish_dataset(mock_s3_client, dataset, output_key)

    mock_s3_client.put_object.assert_awaited_once()
    assert mock_s3_client.put_object.await_args.kwargs["key"] == output_key
    assert isinstance(mock_s3_client.put_object.await_args.kwargs["body"], bytes)
    assert mock_s3_client.put_object.await_args.kwargs["body"]

    generate_cog_spy.assert_called_once()
    assert generate_cog_spy.call_args.kwargs["output_path"] == expected_cog_key
    assert generate_cog_spy.call_args.kwargs["input_path"].endswith("temperature_20240704.tif")

    assert published.output_key == output_key
    assert published.cog_key == expected_cog_key


@pytest.mark.anyio
async def test_publish_dataset_can_skip_cog_generation(mocker):
    output_key = "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
    generate_cog_spy = mocker.patch("wps_sfms.publish.generate_web_optimized_cog")

    mock_s3_client = MagicMock()
    mock_s3_client.put_object = AsyncMock()

    gdal_ds = create_test_dataset(
        "temperature_20240704.tif",
        1,
        1,
        (-1.0, 1.0, -1.0, 1.0),
        4326,
        fill_value=12.5,
        no_data_value=-9999.0,
    )

    with WPSDataset(ds_path=None, ds=gdal_ds) as dataset:
        published = await publish_dataset(
            mock_s3_client,
            dataset,
            output_key,
            generate_cog=False,
        )

    mock_s3_client.put_object.assert_awaited_once()
    generate_cog_spy.assert_not_called()
    assert published.output_key == output_key
    assert published.cog_key is None
