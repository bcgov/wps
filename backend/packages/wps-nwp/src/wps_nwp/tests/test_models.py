from datetime import UTC, datetime

import pytest

from wps_nwp import AIFS, GDPS, GFS, HRDPS, IFS, NAM, RDPS, RRFS, Native, Variable
from wps_nwp.models import Part, parse_idx

RUN = datetime(2026, 11, 4, 12, tzinfo=UTC)

IFS_INDEX = b"""\
{"domain": "g", "date": "20261104", "time": "1200", "step": "3", "levtype": "sfc", "param": "tp", "_offset": 100, "_length": 40}
{"domain": "g", "date": "20261104", "time": "1200", "step": "3", "levtype": "sfc", "param": "2t", "_offset": 500, "_length": 30}
{"domain": "g", "date": "20261104", "time": "1200", "step": "3", "levelist": "850", "levtype": "pl", "param": "t", "_offset": 900, "_length": 20}
{"domain": "g", "date": "20261104", "time": "1200", "step": "3", "levelist": "500", "levtype": "pl", "param": "t", "_offset": 920, "_length": 25}
"""

GFS_IDX = b"""\
1:0:d=2026110412:PRMSL:mean sea level:9 hour fcst:
2:1000:d=2026110412:TMP:2 mb:9 hour fcst:
3:2500:d=2026110412:TMP:2 m above ground:9 hour fcst:
4:4000:d=2026110412:APCP:surface:6-9 hour acc fcst:
5:4600:d=2026110412:APCP:surface:0-9 hour acc fcst:
6.1:5000:d=2026110412:UGRD:10 m above ground:9 hour fcst:
6.2:5000:d=2026110412:VGRD:10 m above ground:9 hour fcst:
7:7000:d=2026110412:RH:2 m above ground:9 hour fcst:
"""


def getter(files: dict[str, bytes]):
    async def get(url: str) -> bytes:
        return files[url]

    return get


@pytest.mark.parametrize(
    "model, step, expected",
    [
        (
            IFS,
            3,
            "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20261104/12z/ifs/0p25/oper/"
            "20261104120000-3h-oper-fc.grib2",
        ),
        (
            AIFS,
            6,
            "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/20261104/12z/aifs-single/0p25/"
            "oper/20261104120000-6h-oper-fc.grib2",
        ),
        (
            GFS,
            9,
            "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20261104/12/atmos/"
            "gfs.t12z.pgrb2.0p25.f009",
        ),
        (
            NAM,
            3,
            "https://noaa-nam-pds.s3.amazonaws.com/nam.20261104/nam.t12z.awphys03.tm00.grib2",
        ),
        (
            RRFS,
            7,
            "https://noaa-rrfs-ops-pds.s3.amazonaws.com/rrfs.20261104/12/"
            "rrfs.t12z.2dfld.13km.f007.na.grib2",
        ),
    ],
)
def test_url_of_indexed_models(model, step, expected):
    assert model.url(model.mirrors[0], RUN, step) == expected


@pytest.mark.parametrize(
    "model, expected",
    [
        (
            GDPS,
            "https://hpfx.collab.science.gc.ca/20261104/WXO-DD/model_gdps/15km/12/003/"
            "20261104T12Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT003H.grib2",
        ),
        (
            RDPS,
            "https://hpfx.collab.science.gc.ca/20261104/WXO-DD/model_rdps/10km/12/003/"
            "20261104T12Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT003H.grib2",
        ),
        (
            HRDPS,
            "https://hpfx.collab.science.gc.ca/20261104/WXO-DD/model_hrdps/continental/2.5km/12/003/"
            "20261104T12Z_MSC_HRDPS_TMP_AGL-2m_RLatLon0.0225_PT003H.grib2",
        ),
    ],
)
@pytest.mark.anyio
async def test_eccc_models_have_one_file_per_variable(model, expected):
    parts = await model.locate(None, model.mirrors[0], RUN, 3, [Variable.T2M])

    assert parts == [Part(Variable.T2M, expected)]
    assert model.probe(model.mirrors[0], RUN, 3) == expected


def test_parse_idx_ignores_blank_lines():
    assert parse_idx("\n1:0:first\n\n2:5:second\n\n") == [
        ("1:0:first", 0, 5, None),
        ("2:5:second", 5, None, None),
    ]


@pytest.mark.anyio
async def test_noaa_locate_leaves_out_variables_the_index_does_not_list():
    mirror = GFS.mirrors[0]
    get = getter({GFS.url(mirror, RUN, 9) + ".idx": GFS_IDX})

    parts = await GFS.locate(get, mirror, RUN, 9, [Variable.D2M, Variable.T2M])

    assert [part.variable for part in parts] == [Variable.T2M]


def test_parse_idx_derives_lengths_from_the_next_message():
    rows = parse_idx(GFS_IDX.decode())

    assert [(offset, length, subfield) for _, offset, length, subfield in rows] == [
        (0, 1000, None),
        (1000, 1500, None),
        (2500, 1500, None),
        (4000, 600, None),
        (4600, 400, None),
        (5000, 2000, 0),  # two fields in one message share its offset and length
        (5000, 2000, 1),
        (7000, None, None),  # nothing follows the last message, so read to the end
    ]


@pytest.mark.anyio
async def test_ecmwf_locate_reads_byte_ranges_from_the_index():
    mirror = IFS.mirrors[0]
    url = IFS.url(mirror, RUN, 3)
    get = getter({IFS.probe(mirror, RUN, 3): IFS_INDEX})
    variables = [Variable.T2M, Variable.PRECIP, Native("t:850")]

    parts = await IFS.locate(get, mirror, RUN, 3, variables)

    assert parts == [
        Part(Variable.T2M, url, 500, 30),
        Part(Variable.PRECIP, url, 100, 40),
        Part(Native("t:850"), url, 900, 20),
    ]


@pytest.mark.anyio
async def test_locate_leaves_out_variables_the_step_does_not_have():
    mirror = IFS.mirrors[0]
    get = getter({IFS.probe(mirror, RUN, 3): IFS_INDEX})

    parts = await IFS.locate(get, mirror, RUN, 3, [Variable.D2M, Variable.T2M])

    assert [part.variable for part in parts] == [Variable.T2M]


@pytest.mark.anyio
async def test_noaa_locate_matches_idx_lines():
    mirror = GFS.mirrors[0]
    url = GFS.url(mirror, RUN, 9)
    get = getter({url + ".idx": GFS_IDX})
    variables = [Variable.T2M, Variable.PRECIP, Variable.V10, Variable.RH2M, Native(":PRMSL:")]

    parts = await GFS.locate(get, mirror, RUN, 9, variables)

    assert parts == [
        Part(Variable.T2M, url, 2500, 1500),  # 2 m above ground, not 2 mb
        Part(Variable.PRECIP, url, 4600, 400),  # the run total, not the 6-9 hour bucket
        Part(Variable.V10, url, 5000, 2000, subfield=1),
        Part(Variable.RH2M, url, 7000, None),
        Part(Native(":PRMSL:"), url, 0, 1000),
    ]


def test_asking_for_a_variable_the_model_lacks_names_the_alternatives():
    with pytest.raises(ValueError, match="ifs does not provide 'rh2m'; it has t2m, d2m"):
        IFS.selector(Variable.RH2M)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "line, model",
    [
        ("6:600:d=2026110412:APCP:surface:0-1 hour acc fcst:", RRFS),
        ("6:600:d=2026110412:APCP:surface:0-7 hour acc fcst:", RRFS),
        ("6:600:d=2026110412:APCP:surface:0-5 day acc fcst:", GFS),
    ],
)
async def test_noaa_precipitation_is_the_total_since_the_run_started(line, model):
    mirror = model.mirrors[0]
    idx = (
        "1:0:d=2026110412:HGT:surface:7 hour fcst:\n"
        "5:400:d=2026110412:APCP:surface:6-7 hour acc fcst:\n" + line + "\n"
    )
    get = getter({model.url(mirror, RUN, 7) + ".idx": idx.encode()})

    parts = await model.locate(get, mirror, RUN, 7, [Variable.PRECIP, Variable.SURFACE_HEIGHT])

    assert [(part.variable, part.offset) for part in parts] == [
        (Variable.PRECIP, 600),
        (Variable.SURFACE_HEIGHT, 0),
    ]


@pytest.mark.anyio
async def test_ecmwf_surface_height_is_the_surface_geopotential_not_a_pressure_level():
    mirror = IFS.mirrors[0]
    index = (
        b'{"param": "z", "levtype": "pl", "levelist": "500", "_offset": 0, "_length": 10}\n'
        b'{"param": "z", "levtype": "sfc", "_offset": 10, "_length": 20}\n'
    )
    get = getter({IFS.probe(mirror, RUN, 0): index})

    (part,) = await IFS.locate(get, mirror, RUN, 0, [Variable.SURFACE_HEIGHT])

    assert (part.offset, part.length) == (10, 20)
