"""Router for SFMS"""

import io
import os
import logging
from fastapi.responses import JSONResponse
import geopandas as gpd
from random import randrange
from datetime import datetime
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, Request, Depends
from app.auth import authentication_required
from app.fire_behaviour.finger_burps import grow_fire_perimeter
from app.risk_map.rep_station import calculate_values_risk, get_fire_perimeter_representative_stations, get_hotspots_nearest_station
from app.schemas.risk import FireShapeStations, GrowInput, ComputeInput, RiskOutput, RiskOutputResponse
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


@router.post("/weather", response_model=FireShapeStations)
async def weather(_=Depends(authentication_required)):
    logger.info("risk-map/grow")
    dirname = os.path.dirname(__file__)
    fire_perims_path = os.path.join(dirname, "PROT_CURRENT_FIRE_POLYS_SP.json")
    start_perim_gdf = gpd.read_file(fire_perims_path)
    representation_stations = await get_fire_perimeter_representative_stations(start_perim_gdf)

    return FireShapeStations(representative_stations=representation_stations)


@router.post("/compute", response_model=RiskOutputResponse)
async def compute(compute_input: ComputeInput, _=Depends(authentication_required)):
    """
    Compute risk stats
    """

    logger.info("risk-map/compute")
    values_gdf = gpd.GeoDataFrame.from_features(compute_input.values.model_dump()["features"], crs="EPSG:4326").to_crs(epsg=3005)
    hotspots_gdf = gpd.GeoDataFrame.from_features(compute_input.hotspots.model_dump()["features"], crs="EPSG:4326").to_crs(epsg=3005)
    res = calculate_values_risk(values_gdf, hotspots_gdf)
    risk_outputs = [RiskOutput(id=row["id"], name=row["Name"], distance=row["distance"], bearing=row["bearing"], direction=row["direction"]) for _, row in res.iterrows()]
    return RiskOutputResponse(risk_outputs=risk_outputs)


@router.post("/grow")
async def grow(grow: GrowInput, request: Request, _=Depends(authentication_required)):
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
            },
            time_of_interest: datetime
            }            
        '
    ```
    """
    logger.info("risk-map/grow")
    days = 4
    distance = 500
    fire_perims = []
    wind_dir = 90
    start_perim_gdf = gpd.GeoDataFrame.from_features(grow.fire_perimeter.model_dump()["features"], crs="EPSG:4326").to_crs(epsg=3005)
    hotspots_gdf = gpd.GeoDataFrame.from_features(grow.hotspots.model_dump()["features"], crs="EPSG:4326").to_crs(epsg=3005)
    hotspots_gdf = await get_hotspots_nearest_station(hotspots_gdf, grow.time_of_interest)

    for idx, _ in enumerate(range(days)):
        prev_prim = start_perim_gdf
        if len(fire_perims) > 0:
            prev_prim = fire_perims[idx - 1]
        new_fire_perimeter = grow_fire_perimeter(prev_prim, hotspots_gdf, wind_angle=wind_dir, distance=distance)
        new_fire_perimeter_gdf = gpd.GeoDataFrame(geometry=[new_fire_perimeter], crs="EPSG:3005")
        fire_perims.append(new_fire_perimeter_gdf)
        distance += randrange(300, 700)
        wind_dir += randrange(-25, 25)

    return JSONResponse(content=[perim.to_crs(epsg=3857).to_json() for perim in fire_perims])
