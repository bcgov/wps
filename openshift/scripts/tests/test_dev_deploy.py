import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "capacity", Path(__file__).resolve().parents[1] / "check_dev_capacity.py"
)
capacity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capacity)


def quota(used):
    return {"status": {"hard": {"requests.memory": "64Gi"}, "used": {"requests.memory": used}}}


class CapacityTests(unittest.TestCase):
    def test_memory_units(self):
        for value in ("1Gi", "1024Mi", "1048576Ki", "1073741824"):
            with self.subTest(value=value):
                self.assertEqual(capacity.memory_bytes(value), 1024**3)
        for value in ("unknown", "NaN", "-1Gi", "1Zi"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                capacity.memory_bytes(value)

    def test_memory_thresholds_for_new_and_existing_environments(self):
        for used, existing, allowed in (
            ("44Gi", False, True),
            ("45057Mi", False, False),
            ("56Gi", True, True),
            ("57345Mi", True, False),
            ("64Gi", True, False),
        ):
            with self.subTest(used=used, existing=existing):
                self.assertEqual(capacity.check_capacity(quota(used), existing)[0], allowed)

    def test_only_a_fully_ready_application_uses_the_update_budget(self):
        for deployment in (
            None,
            {"spec": {"replicas": 2}},
            {"spec": {"replicas": 2}, "status": {"readyReplicas": 1}},
            {"spec": {"replicas": 0}},
        ):
            with self.subTest(deployment=deployment):
                self.assertFalse(capacity.has_ready_application(deployment))
        self.assertTrue(
            capacity.has_ready_application(
                {"spec": {"replicas": 2}, "status": {"readyReplicas": 2}}
            )
        )

    def test_missing_quota_data_is_an_error(self):
        with self.assertRaises(KeyError):
            capacity.check_capacity({"status": {"hard": {}, "used": {}}}, False)

    @patch.object(capacity.subprocess, "run")
    def test_cli_reads_only_dev_and_reports_the_deployment_decision(self, run):
        for used, expected in (("56Gi", "true"), ("57Gi", "false")):
            with self.subTest(used=used), tempfile.TemporaryDirectory() as directory:
                run.reset_mock()
                run.side_effect = [
                    subprocess.CompletedProcess([], 0, stdout=json.dumps(quota(used))),
                    subprocess.CompletedProcess(
                        [],
                        0,
                        stdout=json.dumps(
                            {"spec": {"replicas": 1}, "status": {"readyReplicas": 1}}
                        ),
                    ),
                ]
                output = Path(directory) / "output"
                report = Path(directory) / "summary"
                with (
                    patch.object(capacity.sys, "argv", ["check_dev_capacity.py", "123"]),
                    patch.dict(
                        os.environ,
                        {
                            "GITHUB_OUTPUT": str(output),
                            "GITHUB_STEP_SUMMARY": str(report),
                        },
                    ),
                    redirect_stdout(io.StringIO()),
                ):
                    capacity.main()
                self.assertEqual(output.read_text(), f"deploy={expected}\n")
                self.assertIn("Required headroom: 8Gi", report.read_text())
                if expected == "false":
                    self.assertIn("Existing resources remain", report.read_text())
                for call in run.call_args_list:
                    self.assertEqual(call.args[0][:4], ["oc", "-n", "e1e498-dev", "get"])

    @patch.object(
        capacity, "oc_get", side_effect=subprocess.CalledProcessError(1, "oc", stderr="Forbidden")
    )
    def test_read_failure_does_not_report_insufficient_capacity(self, oc_get):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with (
                patch.object(capacity.sys, "argv", ["check_dev_capacity.py", "123"]),
                patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}),
                self.assertRaises(subprocess.CalledProcessError),
            ):
                capacity.main()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
