"""Download model surface fields and sample elevations at weather station locations."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import xarray as xr
from affine import Affine
from herbie import Herbie
from osgeo import gdal
from pyproj import CRS, Transformer
from weather_model_jobs.ecmwf_model_processor import (
    crop_to_bc,
    get_stations_dataframe,
    sample_station_points,
)
from weather_model_jobs.utils.process_grib import read_station_grid_value
from wps_shared.geospatial.bounds import (
    BC_MAX_LATITUDE,
    BC_MAX_LONGITUDE,
    BC_MIN_LATITUDE,
    BC_MIN_LONGITUDE,
)
from wps_shared.geospatial.geospatial import NAD83_CRS, get_transformer
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import download
from wps_shared.weather_models.eccc_url_fetcher import ECCCUrlFetcher

logger = logging.getLogger(__name__)
GRAVITY = 9.80665


@dataclass(frozen=True)
class SurfaceField:
    """ECCC surface height field and forecast lead in hours used for model elevation."""

    path: str
    grid: str
    forecast_hour: int
    field: str


ECCC_SURFACE_FIELDS: dict[str, SurfaceField] = {
    "HRDPS": SurfaceField(
        path="continental/2.5km",
        grid="RLatLon0.0225",
        forecast_hour=1,
        field="HGT_Sfc",
    ),
    "RDPS": SurfaceField(
        path="10km",
        grid="RLatLon0.09",
        forecast_hour=0,
        field="GeopotentialHeight_Sfc",
    ),
    "GDPS": SurfaceField(
        path="15km",
        grid="LatLon0.15",
        forecast_hour=0,
        field="GeopotentialHeight_Sfc",
    ),
}


def surface_url(model: str, run: datetime) -> str:
    """Return the surface height URL for a UTC ECCC or GFS run."""
    if model == "GFS":
        return gfs_surface_url(run)
    return eccc_surface_url(model, run)


def gfs_surface_url(run: datetime) -> str:
    """Return the GFS surface height URL for forecast hour zero of a UTC run.

    The NOMADS request uses the same BC bounds as weather ingestion.
    """
    params = {
        "dir": f"/gfs.{run:%Y%m%d}/{run.hour:02d}/atmos",
        "file": f"gfs.t{run.hour:02d}z.pgrb2.0p25.f000",
        "var_HGT": "on",
        "lev_surface": "on",
        "subregion": "",
        "toplat": BC_MAX_LATITUDE,
        "leftlon": BC_MIN_LONGITUDE,
        "rightlon": BC_MAX_LONGITUDE,
        "bottomlat": BC_MIN_LATITUDE,
    }
    return f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?{urlencode(params)}"


def eccc_surface_url(model: str, run: datetime) -> str:
    """Return the full grid surface height URL for a UTC ECCC run."""
    settings = ECCC_SURFACE_FIELDS[model]
    return (
        f"https://dd.weather.gc.ca/today/model_{model.lower()}/{settings.path}/"
        f"{run.hour:02d}/{settings.forecast_hour:03d}/"
        f"{run:%Y%m%dT%HZ}_MSC_{model}_{settings.field}_{settings.grid}_"
        f"PT{settings.forecast_hour:03d}H.grib2"
    )


def validate_surface(dataset: gdal.Dataset, model: str) -> None:
    """Require one surface geopotential band for ECMWF, or surface height otherwise.

    Raise ValueError for an unexpected band count, level, parameter, or units.
    """
    if dataset.RasterCount != 1:
        raise ValueError("expected one surface elevation field")
    metadata = dataset.GetRasterBand(1).GetMetadata()
    if metadata["GRIB_SHORT_NAME"] != "0-SFC":
        raise ValueError("expected a surface elevation field")
    element, units = metadata["GRIB_ELEMENT"], metadata["GRIB_UNIT"]
    expected = {("GP", "[(m^2)/(s^2)]")} if model == "ECMWF" else {("HGT", "[gpm]"), ("HGT", "[m]")}
    if (element, units) not in expected:
        raise ValueError("unexpected surface elevation parameter or units")


def sample_grid_elevations(
    dataset: gdal.Dataset, transformer: Transformer, stations: list[WeatherStation]
) -> dict[int, float | None]:
    """Return model heights in metres at station locations, keyed by station code.

    Use the same grid cells as Canadian and GFS weather ingestion. Return None
    for uncovered cells, nodata, or nonfinite values.
    """
    transform = Affine.from_gdal(*dataset.GetGeoTransform())
    band = dataset.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    elevations: dict[int, float | None] = {}
    for station in stations:
        elevations[station.code] = None
        raw_value = read_station_grid_value(band, station, transform, transformer)
        if raw_value is None:
            continue
        sampled = float(raw_value)
        if math.isfinite(sampled) and sampled != nodata:
            elevations[station.code] = sampled
    return elevations


def sample_ecmwf(
    path: Path, transformer: Transformer, stations: list[WeatherStation]
) -> dict[int, float | None]:
    """Return ECMWF model heights in metres at stations, keyed by station code.

    Use weather ingestion's BC crop and nearest cell selection. Convert surface
    geopotential to height using standard gravity. Return None for nonfinite values.
    """
    with xr.open_dataset(
        path,
        engine="cfgrib",
        # an empty path disables .idx files, which we don't reuse for temporary downloads
        backend_kwargs={"indexpath": ""},
    ) as dataset:
        stations_df = get_stations_dataframe(transformer, stations)
        selected = sample_station_points(crop_to_bc(dataset), stations_df)
        elevations = {}
        for station in stations:
            value = float(selected.z.sel(point_code=station.code).item()) / GRAVITY
            elevations[station.code] = value if math.isfinite(value) else None
        return elevations


class ModelElevationSampler:
    """Download model surface fields and sample elevations at station locations.

    Use the caller's directory for downloads. The caller removes the files.
    """

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def download_and_sample(
        self, model: str, run: datetime, stations: list[WeatherStation]
    ) -> dict[int, float | None]:
        """Return model elevations in metres, keyed by station code, for a UTC run.

        Use weather ingestion's coordinate transformation and cell selection.
        Return None for missing sampled values. Errors propagate to the caller.
        """
        path = self._download(model, run)
        elevations = self._sample(model, path, stations)
        return elevations

    def _download(self, model: str, run: datetime) -> Path:
        """Download a run's surface elevation field and return the local GRIB path."""
        if model == "ECMWF":
            path = self._download_ecmwf(run)
        else:
            path = self._download_http(model, run)
        return path

    def _sample(
        self, model: str, path: Path, stations: list[WeatherStation]
    ) -> dict[int, float | None]:
        """Validate a local surface GRIB and return station model elevations in metres.

        Use weather ingestion's coordinate transformation and cell selection.
        Missing samples are returned as None.
        """
        with gdal.Open(str(path)) as dataset:
            validate_surface(dataset, model)
            transformer = get_transformer(NAD83_CRS, CRS.from_wkt(dataset.GetProjection()))
            if model == "ECMWF":
                return sample_ecmwf(path, transformer, stations)
            return sample_grid_elevations(dataset, transformer, stations)

    def _download_http(self, model: str, run: datetime) -> Path:
        """Download an ECCC or GFS surface height GRIB using the weather downloader.

        Reuse provider cache settings and ECCC's mirror fallback. Return the downloaded
        path, or raise FileNotFoundError when the surface field is unavailable.
        """
        url = surface_url(model, run)
        logger.info("Downloading station elevations %s", url)
        if model in ECCC_SURFACE_FIELDS:
            fetcher = ECCCUrlFetcher(run, run.hour)
            cache_config_var = "REDIS_CACHE_ENV_CANADA"
            cache_expiry_config_var = "REDIS_ENV_CANADA_CACHE_EXPIRY"
        else:
            fetcher = None
            cache_config_var = "REDIS_CACHE_NOAA"
            cache_expiry_config_var = "REDIS_NOAA_CACHE_EXPIRY"
        downloaded = download(
            url,
            str(self.directory),
            cache_config_var,
            model,
            cache_expiry_config_var,
            fetcher=fetcher,
        )
        if downloaded is None:
            raise FileNotFoundError(f"surface elevation unavailable: {url}")
        path = Path(downloaded)
        return path

    def _download_ecmwf(self, run: datetime) -> Path:
        """Download IFS oper surface geopotential for a UTC run and return its GRIB path.

        Request lead zero on the 0.1 degree grid with Herbie's default source order.
        """
        source = Herbie(
            run,
            model="ifs",
            product="oper",
            resolution="0p1",
            levtype="sfc",
            fxx=0,
            save_dir=self.directory,
            verbose=False,
        )
        downloaded = source.download(r"^:z:", errors="raise", verbose=False)
        if downloaded is None:
            raise FileNotFoundError(f"IFS surface geopotential unavailable: {run.isoformat()}")
        return Path(downloaded)
