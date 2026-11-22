import sqlite3
import unittest
from contextlib import closing

from tools.session_timer import capture, save


class SessionTimerTest(unittest.TestCase):
    def test_clock_and_phase_markers(self):
        answers = iter(["", "Connecting", "Preparing resources", ""])
        times = iter([100, 110, 170, 190])
        _, total, marks = capture(lambda _: next(answers), lambda: next(times))
        self.assertEqual(total, 90)
        self.assertEqual(marks, [("Connecting", 10), ("Preparing resources", 70)])

    def test_baseline_is_scoped_to_context_and_excludes_current_run(self):
        with closing(sqlite3.connect(":memory:")) as db:
            self.assertEqual(save(db, "startup", ("t1", 30, [("Connecting", 5)])), [])
            self.assertEqual(save(db, "file-import", ("t2", 10, [])), [])
            self.assertEqual(save(db, "STARTUP", ("t3", 45, [])), [30])
            self.assertEqual(
                db.execute("SELECT * FROM load_phase_marks").fetchall(),
                [(1, "Connecting", 5)],
            )


if __name__ == "__main__":
    unittest.main()
