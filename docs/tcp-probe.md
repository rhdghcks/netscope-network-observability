# TCP connection probe

NetScope uses the Python 3 standard library to record individual TCP connection attempts. Run the command from the repository root, specifying the host and port you want to check:

```sh
python tools/tcp_probe.py example.com 443
```

Each run prints a JSON record and appends the same measurement to `netscope.sqlite3` in the current directory. Use `--db` to choose another database path. Its parent directory must already exist.

To inspect recent measurements:

```sql
SELECT observed_at, host, port, elapsed_ms, ok, error
FROM tcp_probes ORDER BY id DESC LIMIT 20;
```

Timestamps use UTC. The elapsed time includes name resolution and the TCP connection attempt. `--timeout 3` sets a socket timeout for each address; DNS resolution and retries across multiple addresses may make the overall measurement take longer.

Exit code `0` means the connection succeeded, `1` means the failed attempt was recorded, and `2` indicates a command-line or storage error. A successful TCP connection does **not** prove that TLS negotiation or an HTTP application is healthy.

The tests use a loopback socket and a temporary SQLite database:

```sh
python -m unittest discover -s tests -v
```
