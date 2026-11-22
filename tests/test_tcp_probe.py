import json
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "tcp_probe.py"


class TcpProbeTest(unittest.TestCase):
    def run_probe(self, port, db, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "127.0.0.1", str(port), "--db", str(db), *extra],
            capture_output=True, text=True, timeout=10,
        )

    def test_records_success_and_refusal_across_runs(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket() as target:
            db = Path(directory) / "history.sqlite3"
            target.bind(("127.0.0.1", 0))
            port = target.getsockname()[1]
            refused = self.run_probe(port, db)
            self.assertEqual(refused.returncode, 1, refused.stderr)
            self.assertFalse(json.loads(refused.stdout)["ok"])
            target.listen()
            success = self.run_probe(port, db)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertTrue(json.loads(success.stdout)["ok"])
            with closing(sqlite3.connect(db)) as conn:
                rows = conn.execute(
                    "SELECT ok, port, error, elapsed_ms FROM tcp_probes ORDER BY id"
                ).fetchall()
            self.assertEqual([row[:2] for row in rows], [(0, port), (1, port)])
            self.assertTrue(rows[0][2])
            self.assertIsNone(rows[1][2])
            self.assertTrue(all(row[3] >= 0 for row in rows))

    def test_invalid_arguments_do_not_create_database(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "history.sqlite3"
            for port, options in [(65536, []), (80, ["--timeout", "nan"])]:
                with self.subTest(port=port):
                    self.assertEqual(self.run_probe(port, db, *options).returncode, 2)
                    self.assertFalse(db.exists())
