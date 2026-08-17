import hashlib
import io
import tarfile
import zipfile

import boto3
import pytest
import responses
from wps_tools.load_testing.deploy_k6_lambda import (
    K6_TARBALL_URL,
    aggregate_summaries,
    build_fan_out_lambda_client,
    build_function_zip,
    build_layer_zip,
    download_k6_binary,
)


def test_build_fan_out_lambda_client_scales_pool_to_concurrency():
    session = boto3.Session(region_name="ca-central-1")

    client = build_fan_out_lambda_client(session, concurrency=250)

    assert client.meta.config.max_pool_connections == 250


def test_build_fan_out_lambda_client_read_timeout_exceeds_lambda_max_duration():
    """Confirmed live: botocore's default read_timeout (60s) is shorter than a synchronous
    invocation that legitimately runs longer (e.g. --hold-seconds 100), so the client gives
    up and reports a spurious failure before the Lambda invocation could possibly return.
    read_timeout must exceed Lambda's own 900s hard per-invocation ceiling."""
    session = boto3.Session(region_name="ca-central-1")

    client = build_fan_out_lambda_client(session, concurrency=10)

    assert client.meta.config.read_timeout > 900


def test_build_fan_out_lambda_client_floors_pool_at_boto3_default():
    """A tiny --concurrency shouldn't shrink the pool below boto3's own default (10) --
    there's no benefit to a smaller pool, and it avoids surprising behavior at low
    concurrency where boto3's own default would otherwise have been used."""
    session = boto3.Session(region_name="ca-central-1")

    client = build_fan_out_lambda_client(session, concurrency=2)

    assert client.meta.config.max_pool_connections == 10


def test_build_layer_zip_contains_k6_with_exec_permission():
    zip_bytes = build_layer_zip(b"fake k6 binary contents")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
        assert zip_file.namelist() == ["opt/k6"]
        assert zip_file.read("opt/k6") == b"fake k6 binary contents"
        info = zip_file.getinfo("opt/k6")
        assert (info.external_attr >> 16) & 0o755 == 0o755


def test_build_function_zip_contains_handler_and_script():
    zip_bytes = build_function_zip(
        b"def handler(event, context): ...", b"export default function () {}", "my_test.js"
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
        assert set(zip_file.namelist()) == {"handler.py", "my_test.js"}
        assert zip_file.read("handler.py") == b"def handler(event, context): ..."
        assert zip_file.read("my_test.js") == b"export default function () {}"


def _summary(
    http_reqs: int, rate_limited: int | None = None, checks_200=(0, 0), checks_429=(0, 0)
) -> dict:
    """Builds a --summary-export-shaped dict matching the real schema confirmed by running
    handler.py locally against the actual AWS Lambda Python base image via podman (see
    README.md) -- not a guessed structure."""
    metrics: dict = {"http_reqs": {"count": http_reqs, "rate": 0}}
    if rate_limited is not None:
        metrics["rate_limited_responses"] = {"count": rate_limited, "rate": 0}
    return {
        "metrics": metrics,
        "root_group": {
            "checks": {
                "status is 200": {"passes": checks_200[0], "fails": checks_200[1]},
                "status is 429 (rate limited)": {"passes": checks_429[0], "fails": checks_429[1]},
            }
        },
    }


def test_aggregate_summaries_sums_across_invocations():
    results = [
        {
            "exit_code": 0,
            "summary": _summary(http_reqs=10, checks_200=(10, 0), checks_429=(0, 10)),
        },
        {
            "exit_code": 0,
            "summary": _summary(http_reqs=10, rate_limited=4, checks_200=(6, 4), checks_429=(4, 6)),
        },
    ]

    assert aggregate_summaries(results) == {
        "invocations": 2,
        "succeeded_invocations": 2,
        "failed_invocations": 0,
        "total_requests": 20,
        "total_rate_limited": 4,
        "checks": {
            "status is 200": {"passes": 16, "fails": 4},
            "status is 429 (rate limited)": {"passes": 4, "fails": 16},
        },
    }


def test_aggregate_summaries_missing_counter_treated_as_zero():
    """Confirmed live (via podman against the real Lambda base image): k6 omits a Counter
    metric entirely from --summary-export when it was never incremented -- an invocation that
    saw zero 429s has no 'rate_limited_responses' key in metrics at all, not count=0. This
    guards against that being mishandled as a KeyError or silently wrong aggregation."""
    results = [
        {"exit_code": 0, "summary": _summary(http_reqs=5, checks_200=(5, 0), checks_429=(0, 5))}
    ]

    assert aggregate_summaries(results)["total_rate_limited"] == 0


def test_aggregate_summaries_skips_invocations_without_a_summary():
    """A timed-out or crashed invocation (handler.py's TimeoutExpired path) has summary=None
    -- it should still count toward invocations/failed_invocations but contribute nothing to
    the request/check totals."""
    results = [
        {"exit_code": 0, "summary": _summary(http_reqs=5, checks_200=(5, 0), checks_429=(0, 5))},
        {"exit_code": None, "summary": None},
    ]

    result = aggregate_summaries(results)

    assert result["invocations"] == 2
    assert result["failed_invocations"] == 1
    assert result["total_requests"] == 5


def test_aggregate_summaries_empty():
    assert aggregate_summaries([]) == {
        "invocations": 0,
        "succeeded_invocations": 0,
        "failed_invocations": 0,
        "total_requests": 0,
        "total_rate_limited": 0,
        "checks": {},
    }


def _make_tarball(member_path: str, content: bytes) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo(name=member_path)
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_download_k6_binary_extracts_and_verifies(mocker):
    tarball_bytes = _make_tarball("k6-v2.2.0-linux-amd64/k6", b"real k6 binary")
    digest = hashlib.sha256(tarball_bytes).hexdigest()
    mocker.patch("wps_tools.load_testing.deploy_k6_lambda.K6_TARBALL_SHA256", digest)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, K6_TARBALL_URL, body=tarball_bytes, status=200)
        extracted = download_k6_binary()

    assert extracted == b"real k6 binary"


def test_download_k6_binary_rejects_checksum_mismatch():
    tarball_bytes = _make_tarball("k6-v2.2.0-linux-amd64/k6", b"tampered binary")

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, K6_TARBALL_URL, body=tarball_bytes, status=200)
        with pytest.raises(RuntimeError, match="unexpected SHA256"):
            download_k6_binary()


def test_download_k6_binary_missing_member_raises(mocker):
    tarball_bytes = _make_tarball("some/other/path", b"wrong file")
    digest = hashlib.sha256(tarball_bytes).hexdigest()
    mocker.patch("wps_tools.load_testing.deploy_k6_lambda.K6_TARBALL_SHA256", digest)

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, K6_TARBALL_URL, body=tarball_bytes, status=200)
        with pytest.raises(KeyError):
            download_k6_binary()
