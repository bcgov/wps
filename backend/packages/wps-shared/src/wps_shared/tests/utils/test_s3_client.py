from io import BufferedReader
import os
import tempfile
import pytest
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.tests.geospatial.dataset_common import create_mock_gdal_dataset
from wps_shared.utils.s3_client import S3Client
from pytest_mock import MockerFixture
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.anyio
async def test_put_object_called(mocker: MockerFixture):
    async with S3Client() as s3_client:
        persist_raster_spy = mocker.patch.object(s3_client, "put_object")
        mock_ds = create_mock_gdal_dataset()
        mock_band: gdal.Band = mock_ds.GetRasterBand(1)
        values = mock_band.ReadAsArray()
        no_data_value = mock_band.GetNoDataValue()

        with tempfile.TemporaryDirectory() as temp_dir:
            with WPSDataset.from_array(values, mock_ds.GetGeoTransform(), mock_ds.GetProjection(), no_data_value) as expected_ds:
                expected_key = "expected_key"
                expected_filename = os.path.join(temp_dir, os.path.basename("expected_key"))
                expected_ds.export_to_geotiff(expected_filename)
                await s3_client.persist_raster_data(temp_dir, expected_key, mock_ds.GetGeoTransform(), mock_ds.GetProjection(), values, no_data_value)

                assert persist_raster_spy.call_args_list == [mocker.call(key=expected_key, body=mocker.ANY)]
                assert isinstance(persist_raster_spy.call_args.kwargs["body"], BufferedReader)


@pytest.mark.anyio
async def test_copy_object_called(mocker: MockerFixture):
    old_key = "old-key"
    new_key = "new-key"
    async with S3Client() as s3_client:
        copy_raster_spy = mocker.patch.object(s3_client, "copy_object")
        await s3_client.copy_object(old_key, new_key)
        copy_raster_spy.assert_called_once_with(old_key, new_key)


@pytest.mark.anyio
async def test_delete_object_called(mocker: MockerFixture):
    old_key = "old-key"
    async with S3Client() as s3_client:
        delete_raster_spy = mocker.patch.object(s3_client, "delete_object")
        await s3_client.delete_object(old_key)
        delete_raster_spy.assert_called_once_with(old_key)


@pytest.mark.anyio
async def test_get_fuel_raster(mocker: MockerFixture):
    sample_data = b"test raster data"

    # Mock the async stream returned by the S3 body
    mock_stream = AsyncMock()
    mock_stream.read.return_value = sample_data
    mock_body_context = MagicMock()
    mock_body_context.__aenter__.return_value = mock_stream

    # Mock the S3 client
    mock_s3_client = AsyncMock()
    mock_s3_client.get_object.return_value = {"Body": mock_body_context}

    # Mock the context manager returned by create_client
    mock_client_context = MagicMock()
    mock_client_context.__aenter__.return_value = mock_s3_client

    # Patch get_session() to return a mocked session
    mock_session = MagicMock()
    mock_session.create_client.return_value = mock_client_context
    mocker.patch("wps_shared.utils.s3_client.get_session", return_value=mock_session)

    async with S3Client() as s3_client:
        response = await s3_client.client.get_object(Bucket="some-bucket", Key="some-key")

        async with response["Body"] as stream:
            data = await stream.read()

        assert data == sample_data


@pytest.mark.anyio
async def test_get_fuel_raster_hash_mismatch(mocker: MockerFixture):
    sample_data = b"test raster data"
    incorrect_hash = "0000"

    # Mock the async stream returned by the S3 body
    mock_stream = AsyncMock()
    mock_stream.read.return_value = sample_data
    mock_body_context = MagicMock()
    mock_body_context.__aenter__.return_value = mock_stream

    # Mock the S3 client
    mock_s3_client = AsyncMock()
    mock_s3_client.get_object.return_value = {"Body": mock_body_context}

    # Mock the context manager returned by create_client
    mock_client_context = MagicMock()
    mock_client_context.__aenter__.return_value = mock_s3_client

    # Patch get_session() to return our mock session
    mock_session = MagicMock()
    mock_session.create_client.return_value = mock_client_context
    mocker.patch("wps_shared.utils.s3_client.get_session", return_value=mock_session)

    async with S3Client() as s3:
        with pytest.raises(ValueError):
            await s3.get_fuel_raster("some-key", incorrect_hash)


@pytest.mark.anyio
async def test_stream_object(mocker: MockerFixture):
    """Test streaming an object without byte range."""
    sample_data = b"test data chunk 1" + b"test data chunk 2"
    test_key = "test/path/file.tif"

    # Mock the async stream that yields chunks
    mock_stream = AsyncMock()
    mock_stream.read.side_effect = [b"test data chunk 1", b"test data chunk 2", b""]
    mock_stream.close = MagicMock()

    # Mock the S3 client
    mock_s3_client = AsyncMock()
    mock_s3_client.get_object.return_value = {
        "Body": mock_stream,
        "ContentLength": len(sample_data),
        "ContentType": "image/tiff",
    }

    # Mock the context manager returned by create_client
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__.return_value = mock_s3_client
    mock_client_context.__aexit__ = AsyncMock()

    # Patch get_session() to return our mock session
    mock_session = MagicMock()
    mock_session.create_client.return_value = mock_client_context
    mocker.patch("wps_shared.utils.s3_client.get_session", return_value=mock_session)

    # Call stream_object
    generator, response = await S3Client.stream_object(test_key)

    # Verify the response metadata
    assert response["ContentLength"] == len(sample_data)
    assert response["ContentType"] == "image/tiff"

    # Verify get_object was called correctly
    mock_s3_client.get_object.assert_called_once_with(Bucket=mocker.ANY, Key=test_key)

    # Consume the generator and verify chunks
    chunks = []
    async for chunk in generator:
        chunks.append(chunk)

    assert chunks == [b"test data chunk 1", b"test data chunk 2"]

    # Verify stream was closed
    mock_stream.close.assert_called_once()

    # Verify client context manager was properly exited
    mock_client_context.__aexit__.assert_called_once()


@pytest.mark.anyio
async def test_stream_object_with_byte_range(mocker: MockerFixture):
    """Test streaming an object with byte range."""
    sample_data = b"partial data"
    test_key = "test/path/file.tif"
    byte_range = "bytes=0-1023"

    # Mock the async stream
    mock_stream = AsyncMock()
    mock_stream.read.side_effect = [sample_data, b""]
    mock_stream.close = MagicMock()

    # Mock the S3 client with range response
    mock_s3_client = AsyncMock()
    mock_s3_client.get_object.return_value = {
        "Body": mock_stream,
        "ContentLength": len(sample_data),
        "ContentRange": "bytes 0-1023/5000",
        "ContentType": "image/tiff",
    }

    # Mock the context manager
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__.return_value = mock_s3_client
    mock_client_context.__aexit__ = AsyncMock()

    # Patch get_session()
    mock_session = MagicMock()
    mock_session.create_client.return_value = mock_client_context
    mocker.patch("wps_shared.utils.s3_client.get_session", return_value=mock_session)

    # Call stream_object with byte range
    generator, response = await S3Client.stream_object(test_key, byte_range=byte_range)

    # Verify the response metadata includes ContentRange
    assert response["ContentRange"] == "bytes 0-1023/5000"

    # Verify get_object was called with Range parameter
    mock_s3_client.get_object.assert_called_once_with(
        Bucket=mocker.ANY, Key=test_key, Range=byte_range
    )

    # Consume the generator
    chunks = []
    async for chunk in generator:
        chunks.append(chunk)

    assert chunks == [sample_data]

    # Verify cleanup
    mock_stream.close.assert_called_once()
    mock_client_context.__aexit__.assert_called_once()


@pytest.mark.anyio
async def test_stream_object_error_handling(mocker: MockerFixture):
    """Test that stream_object properly cleans up on error."""
    test_key = "test/path/file.tif"

    # Mock the S3 client to raise an error
    mock_s3_client = AsyncMock()
    mock_s3_client.get_object.side_effect = Exception("S3 error")

    # Mock the context manager
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__.return_value = mock_s3_client
    mock_client_context.__aexit__ = AsyncMock()

    # Patch get_session()
    mock_session = MagicMock()
    mock_session.create_client.return_value = mock_client_context
    mocker.patch("wps_shared.utils.s3_client.get_session", return_value=mock_session)

    # Verify that exception is raised and client is cleaned up
    with pytest.raises(Exception, match="S3 error"):
        await S3Client.stream_object(test_key)

    # Verify client context manager was properly exited even on error
    mock_client_context.__aexit__.assert_called_once()
