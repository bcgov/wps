from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import numpy as np
import pytest
from affine import Affine
from osgeo import gdal
from pyproj import CRS
from weather_model_jobs import model_elevation_sampler as sampler_module
from weather_model_jobs.utils.process_grib import GribFileProcessor
from wps_shared.geospatial.geospatial import NAD83_CRS, get_transformer
from wps_shared.schemas.stations import WeatherStation

RUN = datetime(2026, 11, 16, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / "fixtures" / "station_elevation"


def station(code: int = 1, **coordinates: float) -> WeatherStation:
    return WeatherStation(
        code=code, name=f"Station {code}", lat=51.375, long=-121.7166667
    ).model_copy(update=coordinates)


@pytest.mark.parametrize(
    "model,hour,token,grid",
    [
        ("HRDPS", 1, "HGT_Sfc", "RLatLon0.0225"),
        ("RDPS", 0, "GeopotentialHeight_Sfc", "RLatLon0.09"),
        ("GDPS", 0, "GeopotentialHeight_Sfc", "LatLon0.15"),
    ],
)
def test_eccc_surface_request(model: str, hour: int, token: str, grid: str) -> None:
    url = sampler_module.surface_url(model, RUN)
    assert url.endswith(f"/{hour:03d}/20261116T00Z_MSC_{model}_{token}_{grid}_PT{hour:03d}H.grib2")


def test_gfs_requests_only_surface_height_in_the_weather_subset() -> None:
    url = sampler_module.surface_url("GFS", RUN)
    params = parse_qs(urlsplit(url).query)
    assert params["file"] == ["gfs.t00z.pgrb2.0p25.f000"]
    assert {key: value for key, value in params.items() if key.startswith(("var_", "lev_"))} == {
        "var_HGT": ["on"],
        "lev_surface": ["on"],
    }
    assert params["leftlon"] == [str(sampler_module.BC_MIN_LONGITUDE)]
    assert params["rightlon"] == [str(sampler_module.BC_MAX_LONGITUDE)]
    assert params["toplat"] == [str(sampler_module.BC_MAX_LATITUDE)]
    assert params["bottomlat"] == [str(sampler_module.BC_MIN_LATITUDE)]


@pytest.mark.parametrize(
    "model,filename,elevation",
    [
        ("HRDPS", "surface_height_rotated.grib2", 1103.6759033203125),
        ("GFS", "surface_height_regular.grib2", 1309.9793701171875),
    ],
)
def test_http_download_and_sample_match_weather(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    filename: str,
    elevation: float,
) -> None:
    path = FIXTURES / filename
    url = sampler_module.surface_url(model, RUN)
    response = Mock(content=path.read_bytes(), url=url, status_code=200)
    fetcher = Mock()
    fetcher.get.return_value = response
    monkeypatch.setattr(sampler_module, "ECCCUrlFetcher", Mock(return_value=fetcher))
    direct_get = Mock(return_value=response)
    monkeypatch.setattr("wps_shared.weather_models.requests.get", direct_get)
    shared_download = Mock(wraps=sampler_module.download)
    monkeypatch.setattr(sampler_module, "download", shared_download)
    monkeypatch.setenv("REDIS_CACHE_ENV_CANADA", "False")
    monkeypatch.setenv("REDIS_CACHE_NOAA", "False")
    stations = [station()]
    result = sampler_module.ModelElevationSampler(tmp_path).download_and_sample(
        model, RUN, stations
    )
    assert result == {1: elevation}
    if model == "GFS":
        direct_get.assert_called_once_with(url, timeout=60)
        fetcher.get.assert_not_called()
        shared_download.assert_called_once_with(
            url, str(tmp_path), "REDIS_CACHE_NOAA", model, "REDIS_NOAA_CACHE_EXPIRY", fetcher=None
        )
    else:
        fetcher.get.assert_called_once_with(url)
        direct_get.assert_not_called()
        shared_download.assert_called_once_with(
            url,
            str(tmp_path),
            "REDIS_CACHE_ENV_CANADA",
            model,
            "REDIS_ENV_CANADA_CACHE_EXPIRY",
            fetcher=fetcher,
        )

    with gdal.Open(str(path)) as dataset:
        transform = Affine.from_gdal(*dataset.GetGeoTransform())
        crs = CRS.from_wkt(dataset.GetProjection())
        monkeypatch.setattr(
            "weather_model_jobs.utils.process_grib.get_stations_synchronously", lambda: stations
        )
        transformer = get_transformer(NAD83_CRS, crs)
        weather = GribFileProcessor(padf_transform=transform, geo_to_raster_transformer=transformer)
        weather_elevations = {
            item.code: float(value)
            for item, value in weather.yield_value_for_stations(dataset.GetRasterBand(1))
        }
        assert result == weather_elevations


@pytest.mark.parametrize(
    "step,coordinates,expected_cell",
    [
        (0.15, (51.375, -121.7166667), (51.3, -121.65)),
        (0.15, (51.7016667, -124.875), (51.75, -124.95)),
        (0.25, (51.375, -121.7166667), (51.25, -121.75)),
    ],
)
def test_lake_stations_keep_the_weather_cell(
    step: float, coordinates: tuple[float, float], expected_cell: tuple[float, float]
) -> None:
    dataset = gdal.GetDriverByName("MEM").Create("", round(360 / step), round(180 / step) + 1)
    dataset.SetGeoTransform((-180 - step / 2, step, 0, 90 + step / 2, 0, -step))
    latitude, longitude = expected_cell
    column = round((longitude + 180) / step)
    row = round((90 - latitude) / step)
    dataset.GetRasterBand(1).WriteArray(np.array([[123]], dtype=np.uint8), column, row)
    result = sampler_module.sample_grid_elevations(
        dataset,
        get_transformer(NAD83_CRS, NAD83_CRS),
        [station(lat=coordinates[0], long=coordinates[1])],
    )
    assert result == {1: 123}


def test_missing_cell_is_not_replaced_by_another_cell() -> None:
    dataset = gdal.GetDriverByName("MEM").Create("", 2, 1, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((-121.75, 0.1, 0, 51.4, 0, -0.1))
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(-9999)
    band.WriteArray(np.array([[-9999, 1234]], dtype=np.float32))
    assert sampler_module.sample_grid_elevations(
        dataset, get_transformer(NAD83_CRS, NAD83_CRS), [station()]
    ) == {1: None}


def test_station_outside_grid_has_null_elevation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    elevation_sampler = sampler_module.ModelElevationSampler(tmp_path)
    download = Mock(return_value=FIXTURES / "surface_height_regular.grib2")
    monkeypatch.setattr(elevation_sampler, "_download", download)
    assert elevation_sampler.download_and_sample("GFS", RUN, [station(lat=60)]) == {1: None}


@pytest.mark.parametrize(
    "bands,metadata,error",
    [
        (1, {"GRIB_ELEMENT": "TMP"}, "parameter"),
        (1, {"GRIB_SHORT_NAME": "2-HTGL"}, "surface"),
        (1, {"GRIB_UNIT": "[K]"}, "units"),
        (2, {}, "one surface"),
    ],
)
def test_reject_wrong_surface_field(bands: int, metadata: dict[str, str], error: str) -> None:
    dataset = Mock(RasterCount=bands)
    dataset.GetRasterBand.return_value.GetMetadata.return_value = {
        "GRIB_SHORT_NAME": "0-SFC",
        "GRIB_ELEMENT": "HGT",
        "GRIB_UNIT": "[gpm]",
    } | metadata
    with pytest.raises(ValueError, match=error):
        sampler_module.validate_surface(dataset, "GFS")


def test_ecmwf_uses_herbie_for_surface_geopotential_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = FIXTURES / "surface_geopotential.grib2"
    herbie_class = sampler_module.Herbie
    monkeypatch.setattr(herbie_class, "find_grib", Mock(return_value=(None, None)))
    monkeypatch.setattr(herbie_class, "find_idx", Mock(return_value=(None, None)))
    download = Mock(return_value=path)
    monkeypatch.setattr(herbie_class, "download", download)
    herbie = Mock(wraps=herbie_class)
    monkeypatch.setattr(sampler_module, "Herbie", herbie)
    result = sampler_module.ModelElevationSampler(tmp_path).download_and_sample(
        "ECMWF", RUN, [station()]
    )
    assert result[1] == pytest.approx(1049.7510378799082, abs=0.0001, rel=0)
    assert herbie.call_args.args == ("2026-11-16 00",)
    assert herbie.call_args.kwargs == {
        "model": "ifs",
        "product": "oper",
        "resolution": "0p1",
        "levtype": "sfc",
        "fxx": 0,
        "save_dir": tmp_path,
        "verbose": False,
    }
    download.assert_called_once_with(r"^:z:", errors="raise", verbose=False)


@pytest.mark.parametrize(
    "model,download_method", [("GFS", "_download_http"), ("ECMWF", "_download_ecmwf")]
)
def test_source_failures_propagate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, model: str, download_method: str
) -> None:
    elevation_sampler = sampler_module.ModelElevationSampler(tmp_path)
    monkeypatch.setattr(
        elevation_sampler, download_method, Mock(side_effect=OSError("unavailable"))
    )
    with pytest.raises(OSError, match="unavailable"):
        elevation_sampler.download_and_sample(model, RUN, [station()])


@pytest.mark.parametrize("model", ["HRDPS", "GFS"])
def test_unavailable_surface_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, model: str
) -> None:
    fetcher = Mock()
    fetcher.get.return_value = None
    monkeypatch.setattr(sampler_module, "ECCCUrlFetcher", Mock(return_value=fetcher))
    monkeypatch.setattr(
        "wps_shared.weather_models.requests.get", Mock(return_value=Mock(status_code=404))
    )
    monkeypatch.setenv("REDIS_CACHE_ENV_CANADA", "False")
    monkeypatch.setenv("REDIS_CACHE_NOAA", "False")
    with pytest.raises(FileNotFoundError, match="surface elevation unavailable"):
        sampler_module.ModelElevationSampler(tmp_path).download_and_sample(model, RUN, [station()])
