import tempfile
import unittest
from pathlib import Path

from distributed_systems_analyzer import analyze_repository


class AnalyzeRepositoryTests(unittest.TestCase):
    def test_reports_gaps_for_a_minimal_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "app.py").write_text("print('hello')\n", encoding="utf-8")

            report = analyze_repository(directory)

            self.assertEqual(report.score, 0)
            self.assertEqual(report.files_scanned, 1)
            self.assertEqual(len(report.gaps), 7)

    def test_scores_distributed_system_evidence_and_finds_risks(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "README.md").write_text(
                "Architecture runbook: stateless workers use shard partition routing.\n"
                "Replication, quorum failover, backup and restore are configured.\n"
                "Use transactions, optimistic lock version checks, outbox deduplication.\n"
                "API version /v1/ has migration support and an event consumer stream.\n"
                "Prometheus metrics, OpenTelemetry tracing, structured logging.\n"
                "Failure test uses fault injection and network partition simulation.\n",
                encoding="utf-8",
            )
            Path(directory, "app.py").write_text(
                "import requests\n"
                "requests.get('http://localhost/data')\n"
                "timeout = 3\n"
                "retry_backoff = True\n"
                "healthcheck = '/healthz'\n"
                "idempotency_key = 'request-id'\n"
                "cache = 'redis'\n"
                "message_queue = 'kafka'\n"
                "config = os.getenv('SERVICE_URL')\n",
                encoding="utf-8",
            )

            report = analyze_repository(directory)

            self.assertGreaterEqual(report.score, 70)
            self.assertTrue(any(item.title == "unbounded network call" for item in report.risks))
            self.assertTrue(any(item.title == "hard-coded loopback dependency" for item in report.risks))
            self.assertIn("Readiness score:", report.render_text())

    def test_ignores_virtual_environment_files(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, ".venv").mkdir()
            Path(directory, ".venv", "noise.py").write_text("timeout = 1\n", encoding="utf-8")
            Path(directory, "main.py").write_text("print('ok')\n", encoding="utf-8")

            report = analyze_repository(directory)

            self.assertEqual(report.files_scanned, 1)
            self.assertEqual(report.score, 0)

    def test_does_not_treat_test_fixture_as_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "tests").mkdir()
            Path(directory, "tests", "test_client.py").write_text(
                "requests.get('http://localhost/data')\n"
                "replication = 'quorum'\n",
                encoding="utf-8",
            )

            report = analyze_repository(directory)

            self.assertFalse(report.risks)
            self.assertFalse(any(item.title == "replication" for item in report.strengths))
            self.assertTrue(any(item.title == "automated tests" for item in report.strengths))

    def test_rejects_missing_repository(self):
        with self.assertRaises(ValueError):
            analyze_repository("/definitely/not/a/repository")


if __name__ == "__main__":
    unittest.main()
