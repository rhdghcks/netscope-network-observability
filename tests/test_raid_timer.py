import sqlite3
import unittest
from contextlib import closing

from tools.raid_timer import capture, save


class RaidTimerTest(unittest.TestCase):
    def test_clock_and_phase_markers(self):
        answers = iter(["", "Matching", "Waiting for players", ""])
        times = iter([100, 110, 170, 190])
        _, total, marks = capture(lambda _: next(answers), lambda: next(times))
        self.assertEqual(total, 90)
        self.assertEqual(marks, [("Matching", 10), ("Waiting for players", 70)])

    def test_baseline_excludes_other_maps_and_current_run(self):
        with closing(sqlite3.connect(":memory:")) as db:
            self.assertEqual(save(db, "Customs", ("t1", 30, [("Matching", 5)])), [])
            self.assertEqual(save(db, "Factory", ("t2", 10, [])), [])
            self.assertEqual(save(db, "customs", ("t3", 45, [])), [30])
            self.assertEqual(db.execute("SELECT * FROM raid_marks").fetchall(),
                             [(1, "Matching", 5)])
