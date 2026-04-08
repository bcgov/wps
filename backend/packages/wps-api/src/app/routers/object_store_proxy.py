"""Object Store Proxy Router

This module provides an endpoint for proxying object files from the
object store.
"""

import logging
from typing import AsyncIterator

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import Response, StreamingResponse
from wps_shared.auth import authentication_required
from wps_shared.utils.s3_client import S3Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/object-store-proxy", dependencies=[Depends(authentication_required)])


class RangeStreamingResponse(StreamingResponse):
    """
    StreamingResponse that automatically handles S3 range responses.

    Processes S3 response metadata to set appropriate HTTP status codes
    and headers for both full (200) and partial (206) content responses.
    """

    def __init__(self, content: AsyncIterator[bytes], s3_response: dict, filename: str, **kwargs):
        """
        Initialize a range-aware streaming response.

        :param content: Async generator yielding response bytes
        :param s3_response: S3 get_object response dict containing metadata
        :param filename: Filename for Content-Disposition header
        :param kwargs: Additional arguments passed to StreamingResponse
        """
        # Determine status code and build headers based on S3 response
        if "ContentRange" in s3_response:
            # Partial content response (206)
            status_code = 206
            content_range = s3_response["ContentRange"]  # e.g. "bytes 0-999/5000"

            # Calculate content length from range
            _, range_str = content_range.split(" ", 1)
            range_part, _ = range_str.split("/")
            start, end = map(int, range_part.split("-"))
            content_length = str(end - start + 1)

            range_headers = {"Content-Range": content_range}
        else:
            # Full content response (200)
            status_code = 200
            content_length = str(s3_response["ContentLength"])
            range_headers = {}

        # Build complete headers
        etag = s3_response.get("ETag", "")
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": s3_response.get("ContentType", "application/octet-stream"),
            "Content-Disposition": f"inline; filename={filename}",
            "Content-Length": content_length,
            "Cache-Control": "private, max-age=3600",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges, Content-Type",
            **range_headers,
            **({"ETag": etag} if etag else {}),
        }

        super().__init__(content, status_code=status_code, headers=headers, **kwargs)


@router.head("/{path:path}")
async def head_s3_object(
    path: str = Path(..., description="Path to the object in the object store"),
):
    """Get metadata for object without downloading it - required for GeoTIFF sources."""
    logger.info(f"HEAD {path}")

    try:
        async with S3Client() as s3_client:
            response = await s3_client.client.head_object(Bucket=s3_client.bucket, Key=path)

            return Response(
                headers={
                    "Content-Type": response.get("ContentType", "application/octet-stream"),
                    "Content-Length": str(response["ContentLength"]),
                    "Accept-Ranges": "bytes",
                    "Access-Control-Expose-Headers": "Content-Length, Accept-Ranges, Content-Type",
                }
            )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"object not found: {path}")
        elif error_code in ("AccessDenied", "Forbidden"):
            raise HTTPException(status_code=403, detail=f"Access denied: {path}")
        raise HTTPException(status_code=502, detail=f"S3 error: {error_code}")


async def _proxy(path: str, byte_range: str | None, stream_fn) -> RangeStreamingResponse:
    """Shared proxy implementation — fetches from S3 via stream_fn and returns a streaming response."""
    filename = path.rsplit("/", 1)[-1]
    try:
        generator, s3_resp = await stream_fn(path, byte_range)
        return RangeStreamingResponse(generator, s3_resp, filename)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"S3 ClientError: {error_code} for {path}")
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"object not found: {path}")
        elif error_code in ("AccessDenied", "Forbidden", "403 Forbidden"):
            raise HTTPException(status_code=403, detail=f"Access denied to object: {path}")
        else:
            raise HTTPException(
                status_code=502, detail=f"Error fetching object from object store: {error_code}"
            )
    except Exception as e:
        logger.error(f"Unexpected error proxying object: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/{path:path}")
async def proxy_s3_object(
    request: Request,
    path: str = Path(..., description="Path to the object file in the object store"),
):
    """
    Proxy GeoTIFF files from the object store.

    Args:
        path: The path/key to the object file in the bucket
              Example: "sfms/calculated/forecast/2025-11-02/fwi20251102.tif"
    """
    logger.info(f"Proxying {path}")
    return await _proxy(path, request.headers.get("range"), S3Client.stream_object)


wx_router = APIRouter(
    prefix="/wx-object-store-proxy", dependencies=[Depends(authentication_required)]
)


@wx_router.get("/{path:path}")
async def proxy_wx_s3_object(
    request: Request,
    path: str = Path(..., description="Path to the PNG file in the WX object store"),
):
    """
    Proxy PNG files from the WX object store (WX_OBJECT_STORE_* config).

    Args:
        path: The path/key to the PNG file in the WX bucket
              Example: "wx_4panel_charts/20260407/model_gdps/15km/00/000/chart.png"
    """
    logger.info(f"Proxying WX object {path}")
    return await _proxy(path, None, S3Client.stream_wx_object)
