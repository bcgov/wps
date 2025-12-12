"""Object Store Proxy Router

This module provides and endpoint for proxying object files from the
object store.
"""

import logging

from fastapi import APIRouter, HTTPException, Path, Request, Depends
from fastapi.responses import StreamingResponse, Response
from botocore.exceptions import ClientError
from wps_shared.utils.s3_client import S3Client
from wps_shared.auth import authentication_required

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/object-store-proxy", dependencies=[Depends(authentication_required)])


@router.head("/{path:path}")
async def head_s3_object(
    path: str = Path(..., description="Path to the file in the object store"),
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
                    "Access-Control-Allow-Origin": "*",
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


@router.get("/{path:path}")
async def proxy_s3_object(
    request: Request,
    path: str = Path(..., description="Path to the GeoTIFF file in the object store"),
):
    """
    Proxy GeoTIFF files from the object store.

    This endpoint acts as a proxy, fetching the file via S3 API and streaming it to the client.

    Args:
        path: The path/key to the object file in the bucket
              Example: "sfms/calculated/forecast/2025-11-02/fwi20251102.tif"

    Returns:
        StreamingResponse containing the GeoTIFF file

    Example:
        GET /api/object-store-proxy/sfms/calculated/forecast/2025-11-02/fwi20251102.tif

        This fetches from:
        s3://{bucket}/sfms/calculated/forecast/2025-11-02/fwi20251102.tif
    """
    logger.info(f"Proxying {path}")

    byte_range = request.headers.get("range")
    filename = path.rsplit("/", 1)[-1]

    try:
        generator, s3_resp = await S3Client.stream_object(path, byte_range)

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": s3_resp.get("ContentType", "application/octet-stream"),
            "Content-Disposition": f"inline; filename={filename}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges, Content-Type",
        }

        # Handle partial
        if "ContentRange" in s3_resp:
            status = 206
            cr = s3_resp["ContentRange"]  # e.g. "bytes 0-999/5000"

            headers["Content-Range"] = cr

            _, rng = cr.split(" ", 1)
            range_part, _ = rng.split("/")
            start, end = map(int, range_part.split("-"))

            headers["Content-Length"] = str(end - start + 1)
        else:
            status = 200
            headers["Content-Length"] = str(s3_resp["ContentLength"])

        return StreamingResponse(generator, status_code=status, headers=headers)

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
