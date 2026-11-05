import aiohttp
import pytest

from wps_nwp import FetchError, NotAvailable
from wps_nwp._http import MAX_RETRY_AFTER_SECONDS, Transport, _retry_after
from wps_nwp.tests.fakes import FakeSession

URL = "https://mirror.test/file.grib2"
OTHER_HOST_URL = "https://elsewhere.test/file.grib2"


def transport(session: FakeSession, retries: int = 2) -> Transport:
    return Transport(concurrency=4, timeout=1, retries=retries, backoff=0, session=session)


@pytest.mark.anyio
async def test_get_whole_file():
    session = FakeSession({URL: b"0123456789"})

    assert await transport(session).get(URL) == b"0123456789"
    assert session.requests == [("GET", URL, None)]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "offset, length, header, expected",
    [(2, 3, "bytes=2-4", b"234"), (0, 4, "bytes=0-3", b"0123"), (7, None, "bytes=7-", b"789")],
)
async def test_get_byte_range(offset, length, header, expected):
    session = FakeSession({URL: b"0123456789"})

    assert await transport(session).get(URL, offset, length) == expected
    assert session.requests == [("GET", URL, header)]


@pytest.mark.anyio
async def test_range_is_cut_locally_when_the_server_sends_the_whole_file():
    session = FakeSession({URL: b"0123456789"}, honour_range=False)

    assert await transport(session).get(URL, 2, 3) == b"234"


@pytest.mark.anyio
async def test_short_response_is_an_error():
    session = FakeSession({URL: b"0123"})

    with pytest.raises(FetchError, match="expected 6 bytes but received 2"):
        await transport(session).get(URL, 2, 6)


@pytest.mark.anyio
@pytest.mark.parametrize("failure", [503, 429, aiohttp.ClientConnectionError("reset")])
async def test_transient_failures_are_retried(failure):
    session = FakeSession({URL: [failure, failure, b"data"]})

    assert await transport(session).get(URL) == b"data"
    assert len(session.requests) == 3


@pytest.mark.anyio
async def test_gives_up_when_retries_run_out():
    session = FakeSession({URL: 503})

    with pytest.raises(FetchError, match="HTTP 503") as raised:
        await transport(session).get(URL)

    assert raised.value.status == 503
    assert len(session.requests) == 3


@pytest.mark.anyio
async def test_missing_file_is_not_retried():
    session = FakeSession({})

    with pytest.raises(NotAvailable):
        await transport(session).get(URL)

    assert len(session.requests) == 1


@pytest.mark.anyio
async def test_client_errors_are_not_retried():
    session = FakeSession({URL: 403})

    with pytest.raises(FetchError, match="HTTP 403"):
        await transport(session).get(URL)

    assert len(session.requests) == 1


@pytest.mark.anyio
async def test_unreachable_host_is_skipped_without_further_requests():
    session = FakeSession({URL: TimeoutError(), OTHER_HOST_URL: b"data"})
    http = transport(session)
    with pytest.raises(FetchError):
        await http.get(URL)
    attempts = len(session.requests)

    with pytest.raises(FetchError, match="mirror.test is unreachable"):
        await http.get(URL)

    assert len(session.requests) == attempts
    assert await http.get(OTHER_HOST_URL) == b"data"


@pytest.mark.anyio
async def test_host_that_answers_with_errors_is_not_marked_unreachable():
    session = FakeSession({URL: [503, 503, 503, b"data"]})
    http = transport(session)
    with pytest.raises(FetchError):
        await http.get(URL)

    assert await http.get(URL) == b"data"


@pytest.mark.anyio
async def test_exists():
    session = FakeSession({URL: b"data"})
    http = transport(session)

    assert await http.exists(URL) is True
    assert await http.exists(OTHER_HOST_URL) is False
    assert [method for method, _, _ in session.requests] == ["HEAD", "HEAD"]


@pytest.mark.parametrize(
    "header, expected",
    [("7", 7.0), ("100000", MAX_RETRY_AFTER_SECONDS), (None, 0.0), ("Wed, 04 Nov 2026", 0.0)],
)
def test_retry_after(header, expected):
    assert _retry_after(header) == expected
