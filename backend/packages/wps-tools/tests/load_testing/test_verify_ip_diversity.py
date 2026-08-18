import io
import zipfile

from wps_tools.load_testing.verify_ip_diversity import (
    build_probe_zip,
    summarize_ip_diversity,
)


def test_build_probe_zip_contains_only_handler():
    zip_bytes = build_probe_zip(b"def handler(event, context): ...")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
        assert zip_file.namelist() == ["handler.py"]
        assert zip_file.read("handler.py") == b"def handler(event, context): ..."


def test_summarize_ip_diversity_counts_distinct_ips():
    results = [
        {"ip": "1.2.3.4"},
        {"ip": "1.2.3.4"},
        {"ip": "5.6.7.8"},
        {"ip": "9.10.11.12"},
    ]

    assert summarize_ip_diversity(results) == {
        "invocations": 4,
        "responses_with_ip": 4,
        "distinct_ips": 3,
        "ip_counts": {"1.2.3.4": 2, "5.6.7.8": 1, "9.10.11.12": 1},
    }


def test_summarize_ip_diversity_all_same_ip():
    """The failure mode this whole tool exists to catch: every invocation funnels through
    the same single IP (e.g. a shared NAT), so 0% real diversity despite N invocations."""
    results = [{"ip": "1.2.3.4"} for _ in range(10)]

    summary = summarize_ip_diversity(results)

    assert summary["distinct_ips"] == 1
    assert summary["ip_counts"] == {"1.2.3.4": 10}


def test_summarize_ip_diversity_skips_failed_invocations():
    """An invocation that errored (handler exception, timeout) has no 'ip' key -- it should
    count toward invocations but not toward responses_with_ip/distinct_ips."""
    results = [{"ip": "1.2.3.4"}, {"errorMessage": "timed out"}, {}]

    summary = summarize_ip_diversity(results)

    assert summary["invocations"] == 3
    assert summary["responses_with_ip"] == 1
    assert summary["distinct_ips"] == 1


def test_summarize_ip_diversity_empty():
    assert summarize_ip_diversity([]) == {
        "invocations": 0,
        "responses_with_ip": 0,
        "distinct_ips": 0,
        "ip_counts": {},
    }
