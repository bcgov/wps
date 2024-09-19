"""Router for SFMS"""

import io
import os
import logging
import json
from fastapi.responses import JSONResponse
import geopandas as gpd
from shapely.geometry import MultiPolygon, mapping
from datetime import datetime
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, UploadFile, Response, Request, BackgroundTasks, Depends
from app.auth import authentication_required, sfms_authenticate
from app.fire_behaviour.finger_burps import grow_fire_perimeter
from app.schemas.risk import FireShapeFeatures
from app.utils.s3 import get_client
from app.utils.time import get_vancouver_now


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/risk-map",
)

RISK_MAP_PERMISSIONS = "public-read"


class FileLikeObject(io.IOBase):
    """Very basic wrapper of the SpooledTemporaryFile to expose the file-like object interface.

    The aiobotocore library expects a file-like object, but we can't pass the SpooledTemporaryFile
    object directly to aiobotocore. aiobotocore looks for a "tell" method, which isn't present
    on SpooledTemporaryFile. aiobotocore doesn't need an object with a tell method, and understands
    how to use IOBase, so we can wrap the SpooledTemporaryFile in a class that implements IOBase
    to make aiobotocore happy.
    """

    def __init__(self, file: SpooledTemporaryFile):
        super().__init__()
        self.file = file

    def read(self, size: int = -1):
        return self.file.read(size)

    def write(self, b: bytes):
        return self.file.write(b)

    def seek(self, offset: int, whence: int = io.SEEK_SET):
        return self.file.seek(offset, whence)


def get_meta_data(request: Request) -> dict:
    """Create the meta-data for the s3 object.
    # NOTE: No idea what timezone this is going to be. Is it UTC? Is it PST? Is it PDT?
    """
    last_modified = datetime.fromisoformat(request.headers.get("Last-modified"))
    create_time = datetime.fromisoformat(request.headers.get("Create-time"))
    return {"last_modified": last_modified.isoformat(), "create_time": create_time.isoformat()}


def get_risk_map_object_store_path(filename: str) -> str:
    """Get the target filename, something that looks like this:
    bucket/sfms/upload/forecast/[issue date NOT TIME]/hfi20220823.tif
    bucket/sfms/upload/actual/[issue date NOT TIME]/hfi20220823.tif
    """
    upload_time = get_vancouver_now()
    unix_timestamp = str(int(upload_time.timestamp()))

    return os.path.join("risk_map", "values", unix_timestamp, filename)


@router.post("/upload")
async def upload(file: UploadFile, request: Request, background_tasks: BackgroundTasks, _=Depends(sfms_authenticate)):
    """
    Trigger the SFMS process to run on the provided file.
    The header MUST include the SFMS secret key.

    ```
    curl -X 'POST' \\
        'https://psu.nrs.gov.bc.ca/api/risk-map/upload' \\
        -H 'accept: application/json' \\
        -H 'Content-Type: multipart/form-data' \\
        -H 'Secret: secret' \\
        -F 'file=@hfi20220812.tif;type=image/tiff'
    ```
    """
    logger.info("risk-map/upload/")
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        # We save the Last-modified and Create-time as metadata in the object store - just
        # in case we need to know about it in the future.
        key = get_risk_map_object_store_path(file.filename)
        logger.info('Uploading file "%s" to "%s"', file.filename, key)
        meta_data = get_meta_data(request)
        await client.put_object(Bucket=bucket, Key=key, Body=FileLikeObject(file.file), Metadata=meta_data)
        await file.close()
        logger.info("Done uploading file")
    return Response(status_code=200)


@router.post("/grow")
async def grow(fire_perimeter: FireShapeFeatures, hotspots: FireShapeFeatures, request: Request, _=Depends(authentication_required)):
    """
    Trigger the SFMS process to run on the provided file.
    The header MUST include the SFMS secret key.
    ```
        curl -X POST "http://127.0.0.1:8000/risk-map/grow" \
        -H "Content-Type: application/json" \
        -d '
            {
            "fire_perimeter": {
                "features": [...]
            },
            "hotspots": {
                "features": [...]
            }
            }            
        '
    ```
    """
    logger.info("risk-map/grow")
    fire_perimeter_gdf = gpd.GeoDataFrame.from_features(fire_perimeter.model_dump()["features"])
    fire_perimeter_gdf = fire_perimeter_gdf.set_crs(3857)
    hotspots_gdf = gpd.GeoDataFrame.from_features(fire_perimeter.model_dump()["features"])
    hotspots_gdf = hotspots_gdf.set_crs(3857)
    new_fire_perimeter = grow_fire_perimeter(fire_perimeter_gdf, hotspots_gdf, 270, distance=500)
    new_fire_perimeter = mapping(new_fire_perimeter)

    return JSONResponse(content=json.dumps(new_fire_perimeter))
