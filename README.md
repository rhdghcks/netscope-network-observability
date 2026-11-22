# NetScope

**Personal network diagnostics and application loading observability**

Sometimes an application takes much longer than usual to start or join an online session. I wanted a way to record those delays instead of relying on memory, compare repeated attempts, and investigate whether connectivity issues happened around the same time.

NetScope is a small, local-first toolkit for collecting evidence about connectivity and loading performance. It is designed to grow from manual measurements into a reusable network observability platform.

## Measure a loading session

Requires Python 3 (standard library only). From the repository root:

```sh
python tools/session_timer.py application-startup
```

Replace `application-startup` with any context that identifies comparable operations, such as `session-join` or `asset-import`.

1. Press Enter when the loading operation starts.
2. Optionally enter labels such as `Connecting` or `Preparing resources` as the displayed phase changes.
3. Press Enter on an empty line once loading completes.

The CLI reports the total elapsed time, optional phase timestamps, and the median duration of previous completed runs for the same context. Completed sessions are saved in the local `netscope.sqlite3` database. Use `--db PATH` to choose another file.

Measurements depend on manual key presses and include human reaction time. They do **not** identify the root cause of a delay or measure internal server processing time.

## Record TCP connectivity

To log a TCP connection attempt:

```sh
python tools/tcp_probe.py example.com 443
```

See [TCP probe documentation](docs/tcp-probe.md) for fields, exit codes, and inspection queries. A successful TCP handshake does not guarantee application availability.

## Run tests

```sh
python -m unittest discover -s tests -v
```

## Direction

The initial tools deliberately keep dependencies minimal. Future iterations can add scheduled probing, time-series correlation, charts, reliable multi-host collection, and failure recovery when they solve observed problems. Network correlation should be supported by measurements rather than assuming every slow application load is caused by the network.
