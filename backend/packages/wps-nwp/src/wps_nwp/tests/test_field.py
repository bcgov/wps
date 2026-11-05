from datetime import UTC, datetime

import numpy as np
import pytest

from wps_nwp import Field, Grid, Native, Variable
from wps_nwp.field import extract
from wps_nwp.tests.fakes import real_grib

RUN = datetime(2026, 11, 4, 12, tzinfo=UTC)
VALUES = np.arange(12, dtype=float).reshape(3, 4)


def field(grib: bytes, variable=Variable.T2M) -> Field:
    return Field("ifs", variable, RUN, 3, "https://mirror.test/file.grib2", grib)


def haversine_nearest(grid: Grid, lats, lons) -> np.ndarray:
    """Nearest grid point by brute force, as an independent check on Grid.nearest."""
    grid_lat, grid_lon = np.radians(grid.lats.ravel()), np.radians(grid.lons.ravel())
    lat, lon = np.radians(lats)[:, None], np.radians(lons)[:, None]
    a = (
        np.sin((grid_lat - lat) / 2) ** 2
        + np.cos(lat) * np.cos(grid_lat) * np.sin((grid_lon - lon) / 2) ** 2
    )
    return a.argmin(axis=1)


def test_decode():
    decoded = field(real_grib(VALUES + 270))

    np.testing.assert_allclose(decoded.values, VALUES + 270, atol=1e-3)
    assert decoded.units == "K"
    assert decoded.grid.shape == (3, 4)
    np.testing.assert_allclose(decoded.grid.lats[:, 0], [60, 59, 58])
    np.testing.assert_allclose(decoded.grid.lons[0], [-130, -129, -128, -127])


def test_missing_values_are_nan():
    values = VALUES.copy()
    values[1, 1] = 9999

    decoded = field(real_grib(values, missing=9999)).values

    assert np.isnan(decoded[1, 1])
    assert np.isnan(decoded).sum() == 1


def test_precipitation_in_metres_is_converted_to_mm():
    grib = real_grib(VALUES / 1000, short_name="tp")

    np.testing.assert_allclose(field(grib, Variable.PRECIP).values, VALUES, atol=1e-3)
    assert field(grib, Variable.PRECIP).units == "mm"


def test_native_fields_are_left_as_the_model_encodes_them():
    native = field(real_grib(VALUES / 1000, short_name="tp"), Native("tp"))

    np.testing.assert_allclose(native.values, VALUES / 1000, atol=1e-6)
    assert native.units == "m"


def test_sample_takes_the_nearest_grid_point():
    decoded = field(real_grib(VALUES))

    sampled = decoded.sample([59.9, 58.4, 59.0], [-129.6, -127.1, -128.4])

    np.testing.assert_allclose(sampled, [0, 11, 6], atol=1e-3)


def test_fields_on_the_same_grid_share_one_grid_and_one_search():
    first, second = field(real_grib(VALUES)), field(real_grib(VALUES + 1))
    lats, lons = [59.2, 58.1], [-129.9, -127.3]

    assert first.grid is second.grid
    assert first.grid.nearest(lats, lons) is second.grid.nearest(lats, lons)


@pytest.mark.parametrize(
    "first_lat, first_lon, rows, columns",
    [(90.0, -180.0, 361, 720), (90.0, 0.0, 361, 720), (62.0, -140.0, 41, 61)],
    ids=["global from -180", "global from 0", "regional"],
)
def test_nearest_agrees_with_brute_force(first_lat, first_lon, rows, columns):
    spacing = 0.5
    lats, lons = np.meshgrid(
        first_lat - spacing * np.arange(rows),
        (first_lon + spacing * np.arange(columns) + 180) % 360 - 180,
        indexing="ij",
    )
    grid = Grid(lats, lons)
    random = np.random.default_rng(0)
    # Points spread over the globe, so most lie far outside the regional grid, then two
    # either side of the date line, two by the poles and two just inside the regional grid.
    point_lats = np.concatenate([random.uniform(-90, 90, 40), [10.0, 10.2, 89.9, -89.9, 50.1, 43]])
    point_lons = np.concatenate(
        [random.uniform(-180, 180, 40), [179.9, -179.9, 45.0, -45.0, -139.8, -110.3]]
    )

    for sample in (slice(None), slice(0, 5), slice(40, 42), slice(42, 44), slice(44, 46)):
        found = grid.nearest(point_lats[sample], point_lons[sample])
        expected = haversine_nearest(grid, point_lats[sample], point_lons[sample])
        np.testing.assert_allclose(lats.ravel()[found], lats.ravel()[expected])
        # At the poles every longitude is the same place, so compare positions on the sphere.
        np.testing.assert_allclose(
            np.cos(np.radians(lats.ravel()[found])) * np.sin(np.radians(lons.ravel()[found])),
            np.cos(np.radians(lats.ravel()[expected])) * np.sin(np.radians(lons.ravel()[expected])),
            atol=1e-12,
        )


def test_nearest_of_nothing():
    grid = field(real_grib(VALUES)).grid

    assert grid.nearest([], []).size == 0


def test_extract_passes_a_whole_message_through():
    grib = real_grib(VALUES)

    assert extract(grib) == grib


@pytest.mark.parametrize("damaged", [b"", b"GRIB", real_grib(VALUES)[:-10], b"<html>503</html>"])
def test_extract_rejects_incomplete_messages(damaged):
    with pytest.raises(ValueError, match="not a complete GRIB message"):
        extract(damaged)


def sections(grib: bytes) -> dict[int, bytes]:
    found, position = {}, 16
    while position < len(grib) - 4:
        length = int.from_bytes(grib[position : position + 4])
        found[grib[position + 4]] = grib[position : position + length]
        position += length
    return found


def test_extract_separates_fields_packed_into_one_message():
    u, v = real_grib(VALUES, short_name="10u"), real_grib(VALUES * -2, short_name="10v")
    # NOAA's packing: the second field repeats only sections 4 to 7.
    body = b"".join(sections(u).values()) + b"".join(sections(v)[n] for n in (4, 5, 6, 7))
    packed = u[:8] + (16 + len(body) + 4).to_bytes(8) + body + b"7777"

    first, second = field(extract(packed, 0), Native("u")), field(extract(packed, 1), Native("v"))

    np.testing.assert_allclose(first.values, VALUES, atol=1e-3)
    np.testing.assert_allclose(second.values, VALUES * -2, atol=1e-3)
    assert second.grid.shape == (3, 4)
    with pytest.raises(ValueError, match="has 2 fields, wanted number 3"):
        extract(packed, 2)
