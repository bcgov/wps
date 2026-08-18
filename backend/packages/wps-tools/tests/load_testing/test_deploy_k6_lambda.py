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
    """The entry must be top-level ("k6"), not nested under "opt/" -- Lambda extracts a
    layer's entire zip directly into /opt/, so an "opt/k6" entry would land at /opt/opt/k6,
    not /opt/k6 where handler.py's K6_BINARY expects it. Confirmed live."""
    zip_bytes = build_layer_zip(b"fake k6 binary contents")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
        assert zip_file.namelist() == ["k6"]
        assert zip_file.read("k6") == b"fake k6 binary contents"
        info = zip_file.getinfo("k6")
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
        "metrics": {
            "http_reqs": {"count": 20},
            "rate_limited_responses": {"count": 4},
        },
        "checks": {
            "status is 200": {"passes": 16, "fails": 4},
            "status is 429 (rate limited)": {"passes": 4, "fails": 16},
        },
    }


def test_aggregate_summaries_missing_counter_omitted_entirely():
    """Confirmed live (via podman against the real Lambda base image): k6 omits a Counter
    metric entirely from --summary-export when it was never incremented -- an invocation that
    saw zero 429s has no 'rate_limited_responses' key in metrics at all, not count=0. Since
    aggregation only reports metrics k6 actually emitted, a Counter that no invocation ever
    touched is simply absent from the aggregate too, not defaulted to count=0."""
    results = [
        {"exit_code": 0, "summary": _summary(http_reqs=5, checks_200=(5, 0), checks_429=(0, 5))}
    ]

    assert "rate_limited_responses" not in aggregate_summaries(results)["metrics"]


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
    assert result["metrics"]["http_reqs"]["count"] == 5


def test_aggregate_summaries_empty():
    assert aggregate_summaries([]) == {
        "invocations": 0,
        "succeeded_invocations": 0,
        "failed_invocations": 0,
        "metrics": {},
        "checks": {},
    }


def test_aggregate_summaries_combines_trend_metrics():
    """Metrics like http_req_duration are Trend-shaped ({"avg":..., "min":..., "max":...}),
    not Counter-shaped -- they can't just be summed. Combining takes min-of-mins,
    max-of-maxes, and an unweighted mean of "avg"."""
    results = [
        {
            "exit_code": 0,
            "summary": {
                "metrics": {"http_req_duration": {"avg": 100, "min": 50, "max": 200}},
                "root_group": {"checks": {}},
            },
        },
        {
            "exit_code": 0,
            "summary": {
                "metrics": {"http_req_duration": {"avg": 200, "min": 20, "max": 500}},
                "root_group": {"checks": {}},
            },
        },
    ]

    metrics = aggregate_summaries(results)["metrics"]

    assert metrics["http_req_duration"] == {"avg": 150, "min": 20, "max": 500}


def test_aggregate_summaries_combines_gauge_metrics():
    """vus is Gauge-shaped ({"value": ...}) -- combining reports the peak (max) value seen
    across invocations, not a sum (summing concurrent VU counts across separate invocations
    would be meaningless)."""
    results = [
        {
            "exit_code": 0,
            "summary": {
                "metrics": {"vus": {"value": 12, "min": 0, "max": 20}},
                "root_group": {"checks": {}},
            },
        },
        {
            "exit_code": 0,
            "summary": {
                "metrics": {"vus": {"value": 30, "min": 0, "max": 30}},
                "root_group": {"checks": {}},
            },
        },
    ]

    metrics = aggregate_summaries(results)["metrics"]

    assert metrics["vus"] == {"value": 30, "min": 0, "max": 30}


def test_aggregate_summaries_averages_http_req_failed_and_checks_rates():
    """Confirmed live (real k6 v2.2.0 --summary-export, 10 Lambda invocations against
    production): http_req_failed and the built-in aggregate "checks" pass rate are both
    Gauge-shaped ({"value": ...}), not Rate-shaped as their names might suggest -- neither has
    a "rate" field at all in this k6 version. Unlike a genuine gauge (e.g. vus), these are
    semantically rates, so combining them across invocations averages instead of taking the
    max -- max would report the worst single invocation's rate as if it were the whole run's."""
    results = [
        {
            "exit_code": 0,
            "summary": {
                "metrics": {"http_req_failed": {"value": 0}, "checks": {"value": 1}},
                "root_group": {"checks": {}},
            },
        },
        {
            "exit_code": 0,
            "summary": {
                "metrics": {"http_req_failed": {"value": 1}, "checks": {"value": 0.6}},
                "root_group": {"checks": {}},
            },
        },
    ]

    metrics = aggregate_summaries(results)["metrics"]

    assert metrics["http_req_failed"] == {"value": pytest.approx(0.5)}
    assert metrics["checks"] == {"value": pytest.approx(0.8)}


def test_aggregate_summaries_combines_bare_rate_metrics():
    """The bare-"rate" fallback branch isn't known to be hit by any real k6 metric (see
    _combine_metric's docstring) but still needs to behave sanely if k6 or a future version
    ever emits one: an unweighted mean across invocations, since there's no per-invocation
    total to weight by."""
    results = [
        {
            "exit_code": 0,
            "summary": {"metrics": {"some_rate": {"rate": 0.1}}, "root_group": {"checks": {}}},
        },
        {
            "exit_code": 0,
            "summary": {"metrics": {"some_rate": {"rate": 0.3}}, "root_group": {"checks": {}}},
        },
    ]

    metrics = aggregate_summaries(results)["metrics"]

    assert metrics["some_rate"]["rate"] == pytest.approx(0.2)


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
