"""Record one TCP connection attempt in a local SQLite database."""

import argparse
import json
import math
import socket
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter


def measure(host, port, timeout):
    observed_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    start = perf_counter()
    error = None
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as exc:
        error = type(exc).__name__ + ": " + str(exc)
    return {
        "observed_at": observed_at,
        "host": host,
        "port": port,
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "ok": error is None,
        "error": error,
    }


def record(path, sample):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS tcp_probes (
                id INTEGER PRIMARY KEY,
                observed_at TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                elapsed_ms REAL NOT NULL,
                ok INTEGER NOT NULL,
                error TEXT
            )
        """)
        db.execute("""
            INSERT INTO tcp_probes (observed_at, host, port, elapsed_ms, ok, error)
            VALUES (:observed_at, :host, :port, :elapsed_ms, :ok, :error)
        """, sample)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("--timeout", type=float, default=3.0,
                        help="socket timeout in seconds per address (default: 3)")
    parser.add_argument("--db", type=Path, default=Path("netscope.sqlite3"))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    sample = measure(args.host, args.port, args.timeout)
    try:
        record(args.db, sample)
    except sqlite3.Error as exc:
        parser.exit(2, f"Could not save measurement to {args.db}: {exc}\n")
    print(json.dumps(sample))
    return 0 if sample["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
