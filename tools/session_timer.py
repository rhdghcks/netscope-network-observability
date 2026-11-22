"""Record a manually observed application loading session with phase markers."""

import argparse
import sqlite3
import statistics
from contextlib import closing
from datetime import datetime, timezone
from time import monotonic


def capture(read=input, clock=monotonic):
    read("Press Enter when the loading sequence begins: ")
    started_at = datetime.now(timezone.utc).isoformat()
    start = clock()
    marks = []
    while True:
        label = read("Enter a phase label, or press Enter when loading completes: ").strip()
        elapsed = clock() - start
        if not label:
            return started_at, elapsed, marks
        marks.append((label, elapsed))


def save(db, context, run):
    started_at, seconds, marks = run
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS load_sessions (
            id INTEGER PRIMARY KEY,
            context TEXT NOT NULL COLLATE NOCASE,
            started_at TEXT NOT NULL,
            duration_seconds REAL NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS load_phase_marks (
            session_id INTEGER NOT NULL REFERENCES load_sessions(id),
            label TEXT NOT NULL,
            elapsed_seconds REAL NOT NULL)""")
        previous = [row[0] for row in db.execute(
            "SELECT duration_seconds FROM load_sessions WHERE context = ?", (context,)
        )]
        session_id = db.execute(
            "INSERT INTO load_sessions(context, started_at, duration_seconds) VALUES (?, ?, ?)",
            (context, started_at, seconds),
        ).lastrowid
        db.executemany(
            "INSERT INTO load_phase_marks VALUES (?, ?, ?)",
            [(session_id, label, elapsed) for label, elapsed in marks],
        )
    return previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", help="label for a comparable workload, e.g. application-startup")
    parser.add_argument("--db", default="netscope.sqlite3")
    args = parser.parse_args()
    context = args.context.strip()
    if not context:
        parser.error("context cannot be empty")
    try:
        run = capture()
        with closing(sqlite3.connect(args.db)) as db:
            previous = save(db, context, run)
    except (EOFError, KeyboardInterrupt):
        parser.exit(1, "\nCancelled; the incomplete session was not saved.\n")
    except sqlite3.Error as exc:
        parser.exit(2, f"Could not save loading session: {exc}\n")

    print(f"{context}: {run[1]:.1f}s total loading time")
    for label, elapsed in run[2]:
        print(f"  +{elapsed:.1f}s  {label}")
    if previous:
        median = statistics.median(previous)
        print(f"Previous {len(previous)} sessions: median {median:.1f}s "
              f"(this session {run[1] - median:+.1f}s)")
    else:
        print("First completed session for this context.")


if __name__ == "__main__":
    main()
