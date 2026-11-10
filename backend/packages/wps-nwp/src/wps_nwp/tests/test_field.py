import sys
from datetime import UTC, datetime

import numpy as np
import pytest

from wps_nwp import Field, Grid, Native, Variable, sample, wind
from wps_nwp.field import extract
from wps_nwp.tests.fakes import fake_grib, real_grib, sample_grib

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


def test_decoding_without_eccodes_says_how_to_get_it(monkeypatch):
    grib = real_grib(VALUES)
    monkeypatch.setitem(sys.modules, "eccodes", None)  # makes "import eccodes" fail

    with pytest.raises(ImportError, match=r"Install wps-nwp\[decode\]"):
        field(grib).values


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


def test_surface_geopotential_is_converted_to_a_height():
    # ECMWF publishes terrain as geopotential: height times standard gravity
    grib = real_grib(VALUES * 1000 * 9.80665, short_name="z")

    np.testing.assert_allclose(field(grib, Variable.SURFACE_HEIGHT).values, VALUES * 1000, atol=0.1)
    assert field(grib, Variable.SURFACE_HEIGHT).units == "m"


def test_surface_height_already_in_metres_is_left_alone():
    grib = real_grib(VALUES * 100, short_name="orog")

    np.testing.assert_allclose(field(grib, Variable.SURFACE_HEIGHT).values, VALUES * 100, atol=0.1)


def test_native_fields_are_left_as_the_model_encodes_them():
    native = field(real_grib(VALUES / 1000, short_name="tp"), Native("tp"))

    np.testing.assert_allclose(native.values, VALUES / 1000, atol=1e-6)
    assert native.units == "m"


def test_sample_takes_the_nearest_grid_point():
    decoded = field(real_grib(VALUES))

    sampled = decoded.sample([59.9, 58.4, 59.0], [-129.6, -127.1, -128.4])

    np.testing.assert_allclose(sampled, [0, 11, 6], atol=1e-3)


def test_sample_does_not_keep_the_decoded_grid():
    decoded = field(real_grib(VALUES))

    sampled = decoded.sample([59.0], [-128.4])

    assert "_decoded" not in vars(decoded)
    np.testing.assert_allclose(sampled, decoded.values[1, 2])
    np.testing.assert_allclose(decoded.sample([59.0], [-128.4]), sampled)


def test_fields_on_the_same_grid_share_one_grid_and_one_search():
    first, second = field(real_grib(VALUES)), field(real_grib(VALUES + 1))
    lats, lons = [59.2, 58.1], [-129.9, -127.3]

    assert first.grid is second.grid
    assert first.grid.nearest(lats, lons) is second.grid.nearest(lats, lons)


def scattered_points(count: int = 40):
    """
    Locations spread over the globe, then two either side of the date line, two by the
    poles and two near 50N 140W.
    """
    random = np.random.default_rng(0)
    lats = np.concatenate([random.uniform(-90, 90, count), [10.0, 10.2, 89.9, -89.9, 50.1, 43]])
    lons = np.concatenate(
        [random.uniform(-180, 180, count), [179.9, -179.9, 45.0, -45.0, -139.8, -110.3]]
    )
    return lats, lons


def assert_same_places(grid: Grid, found, expected):
    """Compare positions rather than indices: at a pole every column is the same place."""
    lats, lons = np.radians(grid.lats.ravel()), np.radians(grid.lons.ravel())
    for index in (found, expected):
        assert index.shape == found.shape
    np.testing.assert_allclose(lats[found], lats[expected])
    np.testing.assert_allclose(
        np.cos(lats[found]) * np.sin(lons[found]),
        np.cos(lats[expected]) * np.sin(lons[expected]),
        atol=1e-12,
    )


@pytest.mark.parametrize(
    "first_lat, first_lon, rows, columns",
    [(90.0, -180.0, 361, 720), (90.0, 0.0, 361, 720), (62.0, -140.0, 41, 61)],
    ids=["global from -180", "global from 0", "regional"],
)
def test_search_of_an_arbitrary_grid_agrees_with_brute_force(first_lat, first_lon, rows, columns):
    spacing = 0.5
    lats, lons = np.meshgrid(
        first_lat - spacing * np.arange(rows),
        (first_lon + spacing * np.arange(columns) + 180) % 360 - 180,
        indexing="ij",
    )
    grid = Grid(lats.shape, lambda: (lats.ravel(), lons.ravel()))
    point_lats, point_lons = scattered_points()

    for subset in (slice(None), slice(0, 5), slice(40, 42), slice(42, 44), slice(44, 46)):
        found = grid.nearest(point_lats[subset], point_lons[subset])
        expected = haversine_nearest(grid, point_lats[subset], point_lons[subset])
        assert_same_places(grid, found, expected)


@pytest.mark.parametrize(
    "layout",
    [
        dict(first_lat=90.0, first_lon=-180.0, shape=(361, 720)),
        dict(first_lat=90.0, first_lon=0.0, shape=(361, 720)),
        dict(first_lat=-90.0, first_lon=0.0, shape=(361, 720), south_to_north=True),
        dict(first_lat=62.0, first_lon=-140.0, shape=(41, 61)),
        dict(first_lat=-12.3, first_lon=-14.8, shape=(59, 115), rotated_south_pole=(-36.1, -114.7)),
        dict(
            first_lat=-48.8,
            first_lon=-53.9,
            shape=(190, 207),
            rotated_south_pole=(-31.8, -92.4),
            south_to_north=True,
        ),
    ],
    ids=[
        "global from -180",
        "global from 0",
        "south to north",
        "regional",
        "rotated",
        "rotated over the pole",
    ],
)
def test_search_of_a_lat_lon_grid_agrees_with_brute_force(layout):
    shape = layout.pop("shape")
    grid = field(real_grib(np.zeros(shape), spacing=0.5, **layout)).grid
    random = np.random.default_rng(1)
    point_lats, point_lons = scattered_points()
    # Also locations known to be on the grid, wherever it is, each nudged off its grid point.
    on_grid = random.integers(0, grid.lats.size, 60)
    point_lats = np.concatenate(
        [point_lats, grid.lats.ravel()[on_grid] + random.uniform(-0.2, 0.2, 60)]
    )
    point_lons = np.concatenate(
        [point_lons, grid.lons.ravel()[on_grid] + random.uniform(-0.2, 0.2, 60)]
    )
    point_lats = np.clip(point_lats, -90, 90)

    found = grid.nearest(point_lats, point_lons)

    assert_same_places(grid, found, haversine_nearest(grid, point_lats, point_lons))


def test_search_copes_with_locations_spread_right_round_the_globe():
    # Low latitudes, so the search box is limited in longitude, yet no box narrower than the
    # whole globe holds all of them.
    lats, lons = np.meshgrid(90.0 - 2 * np.arange(91), -180.0 + 2 * np.arange(180), indexing="ij")
    grid = Grid(lats.shape, lambda: (lats.ravel(), lons.ravel()))
    point_lats = np.array([10.3, 20.7, -10.2, 0.4, 5.9])
    point_lons = np.array([-170.2, -90.6, 0.3, 90.1, 170.8])

    found = grid.nearest(point_lats, point_lons)

    assert_same_places(grid, found, haversine_nearest(grid, point_lats, point_lons))


@pytest.mark.parametrize(
    "grib",
    [
        pytest.param(lambda: sample_grib("regular_gg_sfc_grib2"), id="gaussian"),
        pytest.param(
            lambda: real_grib(
                np.zeros((59, 115)),
                first_lat=-12.3,
                first_lon=-14.8,
                spacing=0.5,
                rotated_south_pole=(-36.1, -114.7),
                rotation_angle=10.0,
            ),
            id="rotated and turned about its own pole",
        ),
    ],
)
def test_grid_without_a_layout_the_fast_search_handles_is_searched_by_its_coordinates(grib):
    grid = field(grib(), Native("t")).grid
    random = np.random.default_rng(2)
    on_grid = random.integers(0, grid.lats.size, 40)
    point_lats = np.clip(grid.lats.ravel()[on_grid] + random.uniform(-0.2, 0.2, 40), -90, 90)
    point_lons = grid.lons.ravel()[on_grid] + random.uniform(-0.2, 0.2, 40)

    found = grid.nearest(point_lats, point_lons)

    assert grid._axes is None
    assert_same_places(grid, found, haversine_nearest(grid, point_lats, point_lons))


def test_sampling_a_lat_lon_grid_does_not_work_out_where_every_point_is():
    decoded = field(real_grib(VALUES + 3, first_lat=20.0, first_lon=30.0))

    decoded.sample([19.2, 18.1], [30.4, 32.9])

    assert "_lat_lon" not in vars(decoded.grid)


def test_grid_spacing_does_not_drift_with_the_rounded_increment():
    # RDPS declares an increment of 0.090298 where its first and last points imply 0.0902978.
    # Stepping by the declared one puts the last of its 1045 rows 0.0002 degrees too far north.
    rows = 1045
    grib = real_grib(
        np.zeros((rows, 2)), first_lat=-48.805954, spacing=0.0902978, south_to_north=True
    )
    grid = field(grib).grid
    just_nearer_the_last_row = grid.lats[-1, 0] - 0.0451

    (found,) = grid.nearest([just_nearer_the_last_row], [-130.0])

    assert found // 2 == rows - 1


@pytest.mark.anyio
async def test_sample_several_fields_in_threads():
    fields = [field(real_grib(VALUES + offset)) for offset in range(6)]
    lats, lons = [59.9, 58.4], [-129.6, -127.1]

    sampled = await sample(fields, lats, lons, workers=3)

    assert len(sampled) == 6
    for offset, values in enumerate(sampled):
        np.testing.assert_allclose(values, np.array([0, 11]) + offset, atol=1e-3)
    assert not any("_decoded" in vars(f) for f in fields)


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


@pytest.mark.parametrize(
    "byte, value",
    [(20, 9), (19, 0)],
    ids=["a section number that does not exist", "a section too short to be one"],
)
def test_extract_rejects_a_message_whose_sections_are_damaged(byte, value):
    damaged = bytearray(fake_grib(b"first", b"second"))
    damaged[byte] = value  # the first section starts at byte 16: four of length, one of number

    with pytest.raises(ValueError, match="malformed GRIB2 message"):
        extract(bytes(damaged), 1)


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


# Placed well east of the rotated frame's origin, as the east of the HRDPS grid is, where its
# axes are turned furthest from true east and north.
ROTATED = dict(first_lat=-1.0, first_lon=20.0, spacing=0.1, rotated_south_pole=(-36.1, -114.7))


def rotated_field(values, short_name: str, relative_to_grid: bool = True) -> Field:
    """A wind component on a 5x5 grid rotated as HRDPS's is."""
    grib = real_grib(values, short_name=short_name, relative_to_grid=relative_to_grid, **ROTATED)
    return field(grib, Native(short_name))


def exact_x_axis_angle(grid: Grid, index) -> np.ndarray:
    """
    The direction of increasing rotated longitude, from the rotation itself rather than from
    neighbouring grid points: the independent check on Grid.x_axis_angle.
    """
    axes = grid._axes
    rows, columns = np.divmod(np.asarray(index), grid.shape[1])
    rotated_lon = np.radians(axes.first_lon + columns * axes.lon_step)
    along = np.stack([-np.sin(rotated_lon), np.cos(rotated_lon), np.zeros(len(rows))], 1)
    along = along @ axes.rotation  # from the rotated frame back to the true one
    lat, lon = np.radians(grid.lats.ravel()[index]), np.radians(grid.lons.ravel()[index])
    east = np.stack([-np.sin(lon), np.cos(lon), np.zeros(len(lon))], 1)
    north = np.stack([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)], 1)
    return np.arctan2((along * north).sum(1), (along * east).sum(1))


def test_x_axis_points_east_on_a_regular_grid():
    grid = field(real_grib(VALUES)).grid

    np.testing.assert_allclose(grid.x_axis_angle(np.arange(12)), 0, atol=1e-12)


def test_x_axis_angle_on_a_rotated_grid_agrees_with_the_rotation():
    grid = rotated_field(np.zeros((5, 5)), "10u").grid
    every_point = np.arange(25)
    edge = np.isin(every_point % 5, (0, 4))  # the first and last columns have one neighbour

    angle = grid.x_axis_angle(every_point)

    exact = exact_x_axis_angle(grid, every_point)
    np.testing.assert_allclose(angle[~edge], exact[~edge], atol=np.radians(0.001))
    np.testing.assert_allclose(angle[edge], exact[edge], atol=np.radians(0.1))
    assert np.degrees(np.abs(angle)).min() > 10  # far enough from east to mean something


@pytest.mark.parametrize(
    "u, v, direction",
    [(0.0, -5.0, 0.0), (-5.0, 0.0, 90.0), (0.0, 5.0, 180.0), (5.0, 0.0, 270.0), (3.0, 4.0, 216.87)],
    ids=["from the north", "from the east", "from the south", "from the west", "south-westerly"],
)
def test_wind_on_a_regular_grid(u, v, direction):
    u_field = field(real_grib(np.full((3, 4), u), short_name="10u"), Variable.U10)
    v_field = field(real_grib(np.full((3, 4), v), short_name="10v"), Variable.V10)

    speed, blowing_from = wind(u_field, v_field, [59.0], [-128.0])

    assert speed == pytest.approx([5.0], abs=1e-3)
    assert min(abs(blowing_from[0] - direction), 360 - abs(blowing_from[0] - direction)) < 0.01
    assert not u_field.relative_to_grid
    assert "_decoded" not in vars(u_field)


def test_wind_relative_to_a_rotated_grid_is_turned_to_true_north():
    # a 10 m/s wind along the grid's y axis, which is not true north on this grid
    u_field, v_field = (
        rotated_field(np.zeros((5, 5)), "10u"),
        rotated_field(np.full((5, 5), 10.0), "10v"),
    )
    index = np.arange(25)
    lats, lons = u_field.grid.lats.ravel(), u_field.grid.lons.ravel()

    speed, blowing_from = wind(u_field, v_field, lats, lons)

    # blowing towards the grid's y axis, which is the x axis turned 90 degrees anticlockwise
    towards = exact_x_axis_angle(u_field.grid, index) + np.pi / 2
    expected = (270 - np.degrees(towards)) % 360
    np.testing.assert_allclose(speed, 10.0, atol=1e-3)
    np.testing.assert_allclose(blowing_from, expected, atol=0.1)
    assert np.abs(blowing_from - 180).min() > 10  # which is not from due south


def test_wind_given_relative_to_true_north_is_not_turned():
    u_field = rotated_field(np.zeros((5, 5)), "10u", relative_to_grid=False)
    v_field = rotated_field(np.full((5, 5), 10.0), "10v", relative_to_grid=False)
    lats, lons = u_field.grid.lats.ravel(), u_field.grid.lons.ravel()

    _, blowing_from = wind(u_field, v_field, lats, lons)

    np.testing.assert_allclose(blowing_from, 180.0, atol=1e-3)


def test_wind_uses_values_that_were_already_decoded():
    u_field = field(real_grib(np.full((3, 4), 5.0), short_name="10u"), Variable.U10)
    v_field = field(real_grib(np.zeros((3, 4)), short_name="10v"), Variable.V10)
    u_field.values  # decodes and keeps the values

    speed, _ = wind(u_field, v_field, [59.0], [-128.0])

    assert speed == pytest.approx([5.0], abs=1e-3)


def test_wind_components_must_be_on_the_same_grid():
    u_field = field(real_grib(np.zeros((3, 4)), short_name="10u"), Variable.U10)
    v_field = rotated_field(np.zeros((5, 5)), "10v")

    with pytest.raises(ValueError, match="different grids"):
        wind(u_field, v_field, [59.0], [-128.0])
