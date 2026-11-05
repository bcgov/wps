import asyncio
import gc
import json
import weakref
from contextlib import aclosing
from datetime import UTC, datetime, timedelta, timezone

import pytest

from wps_nwp import GDPS, GFS, IFS, NAM, Client, FetchError, Native, NotAvailable, Variable
from wps_nwp.field import extract
from wps_nwp.tests.fakes import FakeSession, fake_grib

RUN = datetime(2026, 11, 4, 12, tzinfo=UTC)
AWS, GOOGLE = IFS.mirrors
HPFX, DD = GDPS.mirrors

T2M, D2M, PRECIP = fake_grib(b"temperature"), fake_grib(b"dewpoint"), fake_grib(b"precipitation")


def client(session: FakeSession, retries: int = 0) -> Client:
    return Client(session=session, retries=retries, backoff=0)


def ifs_step(mirror: str, step: int, fields: dict[str, bytes], gap: bytes = b"") -> dict:
    """Routes for one IFS step holding fields back to back, optionally with gap before each."""
    grib, index = b"", ""
    for param, message in fields.items():
        grib += gap
        entry = {"param": param, "levtype": "sfc", "_offset": len(grib), "_length": len(message)}
        index += json.dumps(entry) + "\n"
        grib += message
    return {IFS.url(mirror, RUN, step): grib, IFS.probe(mirror, RUN, step): index.encode()}


@pytest.mark.anyio
async def test_fetch_returns_fields_by_step_then_variable():
    session = FakeSession(
        ifs_step(AWS, 0, {"2t": T2M, "tp": PRECIP}, gap=b"....")
        | ifs_step(AWS, 3, {"tp": PRECIP, "2t": D2M}, gap=b"....")
    )

    async with client(session) as nwp:
        fields = await nwp.fetch("ifs", RUN, [3, 0], ["t2m", Variable.PRECIP])

    assert [(f.step, f.variable, f.grib) for f in fields] == [
        (3, Variable.T2M, D2M),
        (3, Variable.PRECIP, PRECIP),
        (0, Variable.T2M, T2M),
        (0, Variable.PRECIP, PRECIP),
    ]
    assert fields[0].model == "ifs"
    assert fields[0].run == RUN
    assert fields[0].valid_time == RUN + timedelta(hours=3)
    assert fields[0].url == IFS.url(AWS, RUN, 3)


@pytest.mark.anyio
async def test_only_the_requested_fields_are_downloaded():
    session = FakeSession(ifs_step(AWS, 3, {"2t": T2M, "2d": D2M, "tp": PRECIP}, gap=b"...."))

    async with client(session) as nwp:
        await nwp.fetch(IFS, RUN, 3, [Variable.T2M, Variable.PRECIP])

    ranges = {byte_range for _, url, byte_range in session.requests if url.endswith(".grib2")}
    first, last = 4, 4 + len(T2M) + 4 + len(D2M) + 4
    assert ranges == {
        f"bytes={first}-{first + len(T2M) - 1}",
        f"bytes={last}-{last + len(PRECIP) - 1}",
    }


@pytest.mark.anyio
async def test_fields_stored_back_to_back_share_a_request():
    session = FakeSession(ifs_step(AWS, 3, {"2t": T2M, "2d": D2M, "tp": PRECIP}))

    async with client(session) as nwp:
        fields = await nwp.fetch(IFS, RUN, 3, [Variable.PRECIP, Variable.D2M, Variable.T2M])

    assert [f.grib for f in fields] == [PRECIP, D2M, T2M]
    assert session.requests[1:] == [
        ("GET", IFS.url(AWS, RUN, 3), f"bytes=0-{len(T2M + D2M + PRECIP) - 1}")
    ]


@pytest.mark.anyio
async def test_fields_packed_into_one_message_are_separated():
    winds = fake_grib(b"u wind", b"v wind")
    url = NAM.url(NAM.mirrors[0], RUN, 3)
    idx = (
        "1:0:d=2026110412:PRES:surface:3 hour fcst:\n"
        "2.1:50:d=2026110412:UGRD:10 m above ground:3 hour fcst:\n"
        "2.2:50:d=2026110412:VGRD:10 m above ground:3 hour fcst:\n"
    )
    session = FakeSession({url: b"x" * 50 + winds, url + ".idx": idx.encode()})

    async with client(session) as nwp:
        u, v = await nwp.fetch("nam", RUN, 3, ["u10", "v10"])

    assert (u.grib, v.grib) == (fake_grib(b"u wind"), fake_grib(b"v wind"))
    assert session.requests[1:] == [("GET", url, "bytes=50-")]


def index_requests(session: FakeSession) -> int:
    return sum(url.endswith(".index") for url in session.urls())


@pytest.mark.anyio
async def test_stream_yields_one_step_at_a_time():
    session = FakeSession(
        ifs_step(AWS, 0, {"2t": T2M, "tp": PRECIP}) | ifs_step(AWS, 3, {"2t": D2M, "tp": PRECIP})
    )

    async with client(session) as nwp:
        steps = [fields async for fields in nwp.stream("ifs", RUN, [0, 3], ["precip", "t2m"])]

    assert sorted([(f.step, f.variable, f.grib) for f in fields] for fields in steps) == [
        [(0, Variable.PRECIP, PRECIP), (0, Variable.T2M, T2M)],
        [(3, Variable.PRECIP, PRECIP), (3, Variable.T2M, D2M)],
    ]


@pytest.mark.anyio
async def test_stream_downloads_no_more_than_a_window_ahead_of_the_caller():
    steps = [0, 3, 6, 9, 12, 15]
    routes = {}
    for step in steps:
        routes |= ifs_step(AWS, step, {"2t": T2M})
    session = FakeSession(routes)
    started = []

    async with client(session) as nwp:
        async for _ in nwp.stream("ifs", RUN, steps, "t2m", window=2):
            await asyncio.sleep(0.01)  # time for every step that is allowed to start to do so
            started.append(index_requests(session))

    assert started == [2, 3, 4, 5, 6, 6]


@pytest.mark.anyio
async def test_stream_lets_go_of_steps_the_caller_has_finished_with():
    steps = [0, 3, 6, 9]
    routes = {}
    for step in steps:
        routes |= ifs_step(AWS, step, {"2t": T2M})
    delivered = []
    still_alive = []

    async with client(FakeSession(routes)) as nwp:
        async for fields in nwp.stream("ifs", RUN, steps, "t2m", window=1):
            gc.collect()
            still_alive.append(sum(field() is not None for field in delivered))
            delivered.append(weakref.ref(fields[0]))

    assert still_alive == [0, 0, 0, 0]


@pytest.mark.anyio
async def test_stream_stops_downloading_when_the_caller_stops():
    steps = [0, 3, 6, 9]
    routes = {}
    for step in steps:
        routes |= ifs_step(AWS, step, {"2t": T2M})
    session = FakeSession(routes)
    tasks_before = asyncio.all_tasks()

    async with client(session) as nwp:
        async with aclosing(nwp.stream("ifs", RUN, steps, "t2m", window=1)) as stream:
            await anext(stream)
        await asyncio.sleep(0.01)

    assert index_requests(session) == 1
    assert asyncio.all_tasks() == tasks_before  # the steps still waiting were abandoned


@pytest.mark.anyio
async def test_stream_raises_once_it_reaches_a_step_that_is_not_published():
    session = FakeSession(ifs_step(AWS, 0, {"2t": T2M}))
    received = []

    async with client(session) as nwp:
        with pytest.raises(NotAvailable, match=r"\+3h: no t2m"):
            async for fields in nwp.stream("ifs", RUN, [0, 3], "t2m", window=1):
                received.append(fields[0].step)

    assert received == [0]


@pytest.mark.anyio
async def test_stream_leaves_out_steps_with_nothing_published():
    session = FakeSession(ifs_step(AWS, 3, {"2t": T2M}))

    async with client(session) as nwp:
        stream = nwp.stream("ifs", RUN, [0, 3, 6], "t2m", skip_missing=True, window=1)
        steps = [fields[0].step async for fields in stream]

    assert steps == [3]


@pytest.mark.anyio
async def test_native_selector():
    session = FakeSession(ifs_step(AWS, 3, {"msl": T2M}))

    async with client(session) as nwp:
        (field,) = await nwp.fetch("ifs", RUN, 3, Native("msl"))

    assert (field.variable, field.grib) == (Native("msl"), T2M)


@pytest.mark.anyio
async def test_next_mirror_is_used_when_the_first_has_not_published_the_step():
    session = FakeSession(ifs_step(GOOGLE, 3, {"2t": T2M}))

    async with client(session) as nwp:
        (field,) = await nwp.fetch("ifs", RUN, 3, "t2m")

    assert field.url == IFS.url(GOOGLE, RUN, 3)


@pytest.mark.anyio
@pytest.mark.parametrize("failure", [500, TimeoutError(), b"not GRIB data"])
async def test_next_mirror_is_used_when_the_first_fails(failure):
    session = FakeSession(
        ifs_step(AWS, 3, {"2t": T2M})
        | {IFS.url(AWS, RUN, 3): failure}
        | ifs_step(GOOGLE, 3, {"2t": T2M})
    )

    async with client(session) as nwp:
        (field,) = await nwp.fetch("ifs", RUN, 3, "t2m")

    assert field.url == IFS.url(GOOGLE, RUN, 3)


@pytest.mark.anyio
async def test_next_mirror_is_used_when_the_first_serves_something_that_is_not_grib():
    garbage = b"x" * len(T2M)  # the length the index promises, so only its content gives it away
    session = FakeSession(ifs_step(AWS, 3, {"2t": garbage}) | ifs_step(GOOGLE, 3, {"2t": T2M}))

    async with client(session) as nwp:
        (field,) = await nwp.fetch("ifs", RUN, 3, "t2m")

    assert field.url == IFS.url(GOOGLE, RUN, 3)


@pytest.mark.anyio
async def test_fetch_error_when_no_mirror_serves_valid_grib():
    garbage = b"x" * len(T2M)
    session = FakeSession(ifs_step(AWS, 3, {"2t": garbage}) | ifs_step(GOOGLE, 3, {"2t": garbage}))

    async with client(session) as nwp:
        with pytest.raises(FetchError, match="not a complete GRIB message") as raised:
            await nwp.fetch("ifs", RUN, 3, "t2m", skip_missing=True)

    assert raised.value.url == IFS.url(GOOGLE, RUN, 3)


@pytest.mark.anyio
async def test_an_unexpected_error_is_raised_as_it_is_rather_than_trying_another_mirror():
    session = FakeSession(
        ifs_step(AWS, 3, {"2t": T2M})
        | {IFS.url(AWS, RUN, 3): RuntimeError("a bug")}
        | ifs_step(GOOGLE, 3, {"2t": T2M})
    )

    async with client(session) as nwp:
        with pytest.raises(RuntimeError, match="a bug"):
            await nwp.fetch("ifs", RUN, 3, "t2m", skip_missing=True)

    assert all(url.startswith(AWS) for url in session.urls())


@pytest.mark.anyio
async def test_a_missing_native_variable_is_named_as_the_caller_wrote_it():
    session = FakeSession(ifs_step(AWS, 3, {"2t": T2M}))

    async with client(session) as nwp:
        with pytest.raises(NotAvailable, match=r"\+3h: no t:850$"):
            await nwp.fetch("ifs", RUN, 3, Native("t:850"))


@pytest.mark.anyio
async def test_fetch_error_when_every_mirror_fails():
    session = FakeSession({IFS.probe(AWS, RUN, 3): 500, IFS.probe(GOOGLE, RUN, 3): 500})

    async with client(session) as nwp:
        with pytest.raises(FetchError, match="HTTP 500"):
            await nwp.fetch("ifs", RUN, 3, "t2m", skip_missing=True)


@pytest.mark.anyio
async def test_step_that_is_not_published_raises_not_available():
    session = FakeSession(ifs_step(AWS, 0, {"2t": T2M}))

    async with client(session) as nwp:
        with pytest.raises(NotAvailable, match=r"ifs 2026-11-04 12Z \+3h: no t2m"):
            await nwp.fetch("ifs", RUN, [0, 3], "t2m")


@pytest.mark.anyio
async def test_skip_missing_returns_what_is_published():
    session = FakeSession(
        ifs_step(AWS, 0, {"2t": T2M}) | ifs_step(AWS, 3, {"2t": T2M, "tp": PRECIP})
    )

    async with client(session) as nwp:
        fields = await nwp.fetch("ifs", RUN, [0, 3, 6], ["t2m", "precip"], skip_missing=True)

    assert [(f.step, f.variable) for f in fields] == [
        (0, Variable.T2M),
        (3, Variable.T2M),
        (3, Variable.PRECIP),
    ]


@pytest.mark.anyio
async def test_variable_absent_from_a_published_step_is_not_looked_for_on_other_mirrors():
    session = FakeSession(ifs_step(AWS, 0, {"2t": T2M}) | ifs_step(GOOGLE, 0, {"2t": T2M}))

    async with client(session) as nwp:
        fields = await nwp.fetch("ifs", RUN, 0, ["t2m", "precip"], skip_missing=True)

    assert [f.variable for f in fields] == [Variable.T2M]
    assert all(url.startswith(AWS) for url in session.urls())


@pytest.mark.anyio
async def test_eccc_falls_back_per_file():
    def url(mirror, variable):
        return GDPS.url(mirror, RUN, 3, var=GDPS.variables[variable])

    session = FakeSession(
        {
            url(HPFX, Variable.T2M): T2M,
            url(HPFX, Variable.D2M): 500,
            url(DD, Variable.D2M): D2M,
        }
    )

    async with client(session) as nwp:
        fields = await nwp.fetch("gdps", RUN, 3, ["t2m", "d2m", "precip"], skip_missing=True)

    assert [(f.variable, f.url) for f in fields] == [
        (Variable.T2M, url(HPFX, Variable.T2M)),
        (Variable.D2M, url(DD, Variable.D2M)),
    ]
    assert url(DD, Variable.T2M) not in session.urls()


@pytest.mark.anyio
async def test_failure_on_the_last_mirror_is_not_reported_as_missing_data():
    url = GDPS.url(DD, RUN, 3, var="AirTemp_AGL-2m")
    session = FakeSession({url: 500})

    async with client(session) as nwp:
        with pytest.raises(FetchError) as raised:
            await nwp.fetch("gdps", RUN, 3, "t2m", skip_missing=True)

    assert raised.value.url == url


@pytest.mark.anyio
@pytest.mark.parametrize(
    "model, run, variables, message",
    [
        ("icon", RUN, "t2m", "unknown model 'icon'"),
        ("ifs", RUN, "rh2m", "ifs does not provide 'rh2m'"),
        ("ifs", RUN, "temperature", "'temperature' is not a valid Variable"),
        ("gdps", RUN.replace(hour=6), "t2m", "gdps runs at 00Z, 12Z, not 06:00Z"),
        ("ifs", RUN.replace(minute=30), "t2m", "ifs runs at 00Z, 06Z, 12Z, 18Z, not 12:30Z"),
    ],
)
async def test_invalid_requests_fail_before_any_request_is_made(model, run, variables, message):
    session = FakeSession({})

    async with client(session) as nwp:
        with pytest.raises(ValueError, match=message):
            await nwp.fetch(model, run, 3, variables)

    assert session.requests == []


@pytest.mark.anyio
@pytest.mark.parametrize(
    "run",
    [datetime(2026, 11, 4, 12), datetime(2026, 11, 4, 4, tzinfo=timezone(timedelta(hours=-8)))],
)
async def test_run_time_is_normalised_to_utc(run):
    session = FakeSession(ifs_step(AWS, 3, {"2t": T2M}))

    async with client(session) as nwp:
        (field,) = await nwp.fetch("ifs", run, 3, "t2m")

    assert field.run == RUN


@pytest.mark.anyio
async def test_latest_run_is_the_newest_cycle_that_has_the_step():
    now = datetime(2026, 11, 4, 20, 15, tzinfo=UTC)
    published = {
        GFS.probe(GFS.mirrors[0], datetime(2026, 11, 4, 18, tzinfo=UTC), 0): b"idx",
        GFS.probe(GFS.mirrors[1], datetime(2026, 11, 4, 12, tzinfo=UTC), 48): b"idx",
        GFS.probe(GFS.mirrors[0], datetime(2026, 11, 4, 6, tzinfo=UTC), 48): b"idx",
    }

    async with client(FakeSession(published)) as nwp:
        assert await nwp.latest_run("gfs", now=now) == datetime(2026, 11, 4, 18, tzinfo=UTC)
        assert await nwp.latest_run("gfs", step=48, now=now) == RUN


@pytest.mark.anyio
async def test_latest_run_gives_up_after_the_lookback():
    now = datetime(2026, 11, 4, 20, tzinfo=UTC)
    session = FakeSession({})

    async with client(session) as nwp:
        with pytest.raises(NotAvailable, match="gdps: no run since 2026-11-03 20Z"):
            await nwp.latest_run("gdps", now=now, lookback=timedelta(days=1))

    probed = [
        GDPS.probe(mirror, run, 0) for run in (RUN, RUN.replace(hour=0)) for mirror in (HPFX, DD)
    ]
    assert session.urls() == probed


@pytest.mark.anyio
async def test_latest_run_does_not_mistake_an_outage_for_an_unpublished_run():
    now = datetime(2026, 11, 4, 13, tzinfo=UTC)
    session = FakeSession({GDPS.probe(HPFX, RUN, 0): 500, GDPS.probe(DD, RUN, 0): 500})

    async with client(session) as nwp:
        with pytest.raises(FetchError):
            await nwp.latest_run("gdps", now=now)


def test_fake_grib_fields_split_like_the_real_thing():
    assert extract(fake_grib(b"a", b"b"), 1) == fake_grib(b"b")
