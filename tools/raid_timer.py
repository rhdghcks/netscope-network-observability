"""Time a raid loading screen from Ready to entry."""

import argparse
import sqlite3
import statistics
from contextlib import closing
from datetime import datetime, timezone
from time import monotonic


def capture(read=input, clock=monotonic):
    read("Press Enter when you click Ready: ")
    started_at = datetime.now(timezone.utc).isoformat()
    start = clock()
    marks = []
    while True:
        label = read("Type a new loading phase, or press Enter when you enter the raid: ").strip()
        elapsed = clock() - start
        if not label:
            return started_at, elapsed, marks
        marks.append((label, elapsed))


def save(db, map_name, run):
    started_at, seconds, marks = run
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS raid_loads (
            id INTEGER PRIMARY KEY, map_name TEXT NOT NULL COLLATE NOCASE,
            started_at TEXT NOT NULL, seconds REAL NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS raid_marks (
            raid_id INTEGER NOT NULL REFERENCES raid_loads(id),
            label TEXT NOT NULL, elapsed_seconds REAL NOT NULL)""")
        raid_id = db.execute(
            "INSERT INTO raid_loads(map_name, started_at, seconds) VALUES (?, ?, ?)",
            (map_name, started_at, seconds),
        ).lastrowid
        previous = [row[0] for row in db.execute(
            "SELECT seconds FROM raid_loads WHERE map_name = ? AND id < ?", (map_name, raid_id)
        )]
        db.executemany("INSERT INTO raid_marks VALUES (?, ?, ?)",
                       [(raid_id, label, elapsed) for label, elapsed in marks])
    return previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", help="map name, e.g. Customs")
    parser.add_argument("--db", default="netscope.sqlite3")
    args = parser.parse_args()
    map_name = args.map.strip()
    if not map_name:
        parser.error("enter a map name")
    try:
        run = capture()
        with closing(sqlite3.connect(args.db)) as db:
            previous = save(db, map_name, run)
    except (EOFError, KeyboardInterrupt):
        parser.exit(1, "\nCancelled before saving the completed load.\n")
    except sqlite3.Error as exc:
        parser.exit(2, f"Could not save raid: {exc}\n")
    print(f"{map_name}: {run[1]:.1f}s from Ready to entry")
    for label, elapsed in run[2]:
        print(f"  +{elapsed:.1f}s  {label}")
    if previous:
        median = statistics.median(previous)
        print(f"Previous {len(previous)} on this map: median {median:.1f}s "
              f"(this raid {run[1] - median:+.1f}s)")
    else:
        print("First completed load on this map.")


if __name__ == "__main__":
    main()
