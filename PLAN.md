# 📐 Technical Plan — System Monitoring Agent

> Version: 1.0.0
> Status: Draft
> Last updated: 2025

---

## 1. Project Goals

Build a Linux background service (`monitoring-agent`) that:

1. Collects CPU, RAM, Disk, and Network statistics periodically
2. Watches specified files/directories for filesystem change events
3. Writes structured log entries to a local log file and/or system syslog
4. Runs as a `systemd` managed service (auto-start, auto-restart)
5. Can be installed and uninstalled via a `.deb` or `.rpm` package

**Non-goals (out of scope for v1.0):**
- Remote metric transport (Prometheus, InfluxDB, etc.)
- Web dashboard or HTTP API
- Multi-host aggregation
- Windows / macOS support

---

## 2. Technology Choices

### Language: Python 3.10+

**Rationale:**
- `psutil` is the de-facto standard for cross-platform system metrics in Python
- `watchdog` wraps Linux `inotify` cleanly with a high-level API
- Python packages map directly to `.deb`/`.rpm` via `fpm` or `stdeb`
- Readable, maintainable code appropriate for a university project

### Libraries

| Library | Purpose | Version |
|---|---|---|
| `psutil` | CPU, RAM, Disk, Network metrics | ≥ 5.9.0 |
| `watchdog` | Filesystem event monitoring (inotify) | ≥ 3.0.0 |
| `PyYAML` | YAML config parsing | ≥ 6.0 |
| `APScheduler` | Periodic job scheduling (optional; can use `time.sleep` loop) | ≥ 3.10.0 |

### Packaging: `fpm`

**Rationale:**
- Language-agnostic: can wrap any Python package into `.deb` or `.rpm`
- Single command-line invocation
- Handles maintainer scripts (`postinstall`, `preremove`)
- Widely used in CI/CD for non-Maven projects

---

## 3. Architecture

### 3.1 Component Overview

```
 ┌──────────────────────────────────────────────────────────────┐
 │                  monitoring-agent (systemd service)          │
 │                                                              │
 │  ┌──────────────┐    ┌────────────────────────────────────┐ │
 │  │  Config      │───▶│         Main Loop (main.py)        │ │
 │  │  (YAML)      │    │   APScheduler / time.sleep cycle   │ │
 │  └──────────────┘    └──────────────┬─────────────────────┘ │
 │                                     │                        │
 │               ┌─────────────────────┼──────────────────┐    │
 │               ▼                     ▼                   ▼    │
 │  ┌────────────────────┐  ┌──────────────────┐  ┌────────────┐│
 │  │   Collectors       │  │   FS Watcher     │  │  Alerter   ││
 │  │  cpu / memory /    │  │  (watchdog)      │  │ thresholds ││
 │  │  disk / network    │  │  inotify events  │  │ WARN log   ││
 │  └────────────┬───────┘  └────────┬─────────┘  └─────┬──────┘│
 │               └─────────────┬─────┘                  │       │
 │                             ▼                         │       │
 │                   ┌──────────────────┐                │       │
 │                   │  Data Aggregator │◀───────────────┘       │
 │                   │  (dict → string) │                        │
 │                   └────────┬─────────┘                        │
 │                            │                                  │
 │               ┌────────────┴───────────────┐                  │
 │               ▼                            ▼                  │
 │  ┌────────────────────┐      ┌─────────────────────────┐      │
 │  │   Log File         │      │   Syslog                │      │
 │  │ /var/log/agent/    │      │ SysLogHandler /dev/log  │      │
 │  │ RotatingFileHandler│      │                         │      │
 │  └────────────────────┘      └─────────────────────────┘      │
 └──────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

1. **Startup:** `main.py` reads `config.yaml`, initialises logger, starts FS watcher observer thread
2. **Every N seconds:** scheduler fires → each collector returns a dict → dicts merged → logged as one line
3. **FS Events:** `watchdog` handler fires on inotify event → logged immediately (out-of-band from scheduler)
4. **Threshold check:** after each collection cycle, `alerter.py` compares values to configured limits
5. **Shutdown:** SIGTERM → observer stopped → scheduler stopped → clean exit

### 3.3 Log Format

```
2025-01-01 12:00:00,000 INFO  [METRICS] cpu=12.5% load=(0.8,0.6,0.5) mem=62.1% disk_root=45.3% net_sent=1024B net_recv=2048B
2025-01-01 12:00:01,123 INFO  [FS] MODIFIED /var/www/html/index.html
2025-01-01 12:00:30,000 WARN  [ALERT] CPU usage 83.2% exceeds threshold 80%
```

---

## 4. Module Descriptions

### `src/monitoring_agent/main.py`

- Parses optional `--config` CLI argument
- Calls `config.load(path)` → returns validated config dict
- Calls `logger.setup(cfg)` → returns configured Python logger
- Starts `fs_watcher.start_watchers(cfg["watch_paths"], log)` → returns `Observer`
- Registers `SIGTERM` / `SIGINT` handlers for graceful shutdown
- Enters main loop: `collect → log → sleep`

### `src/monitoring_agent/config.py`

- `load(path: str) -> dict` — reads YAML, applies defaults for missing keys, raises `ConfigError` on invalid values
- Defaults: `interval_seconds=60`, `syslog=false`, `level=INFO`
- Validates: paths exist (warn if not), thresholds in 0–100 range

### `src/monitoring_agent/logger.py`

- `setup(cfg: dict) -> logging.Logger` — creates logger named `monitoring_agent`
- Adds `RotatingFileHandler` (file path, max_bytes, backup_count from config)
- Optionally adds `SysLogHandler` if `logging.syslog: true`
- Format: `%(asctime)s %(levelname)-5s %(message)s`

### `src/monitoring_agent/collectors/cpu.py`

- `collect() -> dict` with keys: `cpu_percent`, `cpu_count`, `load_avg` (tuple)
- Uses `psutil.cpu_percent(interval=1)` and `psutil.getloadavg()`

### `src/monitoring_agent/collectors/memory.py`

- `collect() -> dict` with keys: `mem_total_mb`, `mem_used_mb`, `mem_percent`
- Uses `psutil.virtual_memory()`

### `src/monitoring_agent/collectors/disk.py`

- `collect() -> dict` — iterates `psutil.disk_partitions()`, collects usage per mountpoint
- Also collects I/O counters via `psutil.disk_io_counters()`

### `src/monitoring_agent/collectors/network.py`

- `collect() -> dict` — per-interface stats from `psutil.net_io_counters(pernic=True)`
- Returns `bytes_sent`, `bytes_recv`, `packets_sent`, `packets_recv` per interface

### `src/monitoring_agent/collectors/fs_watcher.py`

- `AgentFSHandler(FileSystemEventHandler)` — logs each event immediately via logger
- `start_watchers(paths, logger) -> Observer` — schedules handler for each configured path

### `src/monitoring_agent/collectors/__init__.py`

- `collect_all(cfg) -> dict` — calls each active collector, merges results into single dict

### `src/monitoring_agent/alerter.py`

- `check(metrics: dict, thresholds: dict, logger)` — compares each metric to its threshold
- Emits `logger.warning(...)` when exceeded; no external notification in v1.0

---

## 5. Configuration Design

Single YAML file at `/etc/monitoring-agent/config.yaml` (installed) or custom path (dev).

Design decisions:
- **YAML over INI:** supports nested keys and lists natively; needed for `watch_paths`
- **Single file:** keeps installation simple; no config directory scanning
- **Defaults in code:** `config.py` provides safe defaults; missing keys don't crash agent

---

## 6. systemd Integration

**Unit file: `systemd/monitoring-agent.service`**

```ini
[Unit]
Description=System Monitoring Agent
After=network.target syslog.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/monitoring-agent --config /etc/monitoring-agent/config.yaml
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal
SyslogIdentifier=monitoring-agent

[Install]
WantedBy=multi-user.target
```

Key decisions:
- `Type=simple`: process does not fork; systemd tracks the main PID
- `Restart=on-failure`: auto-restart on crash but not on clean `systemctl stop`
- `User=root`: required for reading `/proc` stats and watching arbitrary paths
- `SyslogIdentifier`: journal tag for `journalctl -u monitoring-agent`

---

## 7. Packaging

### 7.1 `setup.py` / `pyproject.toml`

```toml
[project]
name = "monitoring-agent"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = ["psutil>=5.9.0", "watchdog>=3.0.0", "PyYAML>=6.0"]

[project.scripts]
monitoring-agent = "monitoring_agent.main:main"
```

The `[project.scripts]` entry creates `/usr/bin/monitoring-agent` automatically.

### 7.2 `.deb` build (`packaging/build_deb.sh`)

```bash
#!/bin/bash
set -e
VERSION="1.0.0"
pip install --target=./build/lib .
fpm -s dir -t deb \
  --name monitoring-agent \
  --version "$VERSION" \
  --architecture amd64 \
  --description "System Monitoring Agent" \
  --maintainer "Student Name <email>" \
  --depends "python3 (>= 3.10)" \
  --after-install packaging/postinstall.sh \
  --before-remove packaging/preremove.sh \
  --prefix / \
  build/lib/=/usr/lib/monitoring-agent/ \
  config/config.yaml.example=/etc/monitoring-agent/config.yaml \
  systemd/monitoring-agent.service=/usr/lib/systemd/system/monitoring-agent.service \
  config/logrotate.conf=/etc/logrotate.d/monitoring-agent
```

### 7.3 `postinstall.sh`

```bash
#!/bin/bash
systemctl daemon-reload
systemctl enable monitoring-agent
mkdir -p /var/log/monitoring-agent
```

### 7.4 `preremove.sh`

```bash
#!/bin/bash
systemctl stop monitoring-agent || true
systemctl disable monitoring-agent || true
```

---

## 8. Testing Strategy

| Test file | What it covers |
|---|---|
| `test_config.py` | Valid YAML, missing keys → defaults, invalid values → error |
| `test_collectors.py` | Each collector returns expected dict keys; mock `psutil` calls |
| `test_alerter.py` | Below threshold → no warn, above threshold → warn logged |
| `test_logger.py` | File handler created, syslog handler added when enabled |
| `test_fs_watcher.py` | Handler called on file write in temp directory |

- Use `pytest` + `unittest.mock` to patch `psutil` — no real metrics needed in unit tests
- Use `pytest-tmp-path` fixture for filesystem watcher tests
- Target ≥ 80% coverage

---

## 9. Development Milestones

### Phase 1 — Core Collectors (Week 1)

- [ ] Project scaffold: `setup.py`, `pyproject.toml`, `requirements.txt`, `.gitignore`
- [ ] `config.py` with defaults and validation
- [ ] `logger.py` with file rotation and optional syslog
- [ ] `collectors/cpu.py`, `collectors/memory.py`, `collectors/disk.py`, `collectors/network.py`
- [ ] `collectors/__init__.py` — `collect_all()`
- [ ] `main.py` — basic loop with `time.sleep`
- [ ] Manual test: run in terminal, observe log output

### Phase 2 — FS Watcher + Alerter (Week 2)

- [ ] `collectors/fs_watcher.py` — Observer + handler
- [ ] Integrate watcher into `main.py` startup
- [ ] `alerter.py` — threshold checks
- [ ] `config/config.yaml.example` — fully commented
- [ ] Unit tests for all modules

### Phase 3 — systemd Service (Week 3)

- [ ] `systemd/monitoring-agent.service`
- [ ] Install manually to `/etc/systemd/system/`, test `systemctl start/stop/restart`
- [ ] Verify journal output: `journalctl -u monitoring-agent -f`
- [ ] `config/logrotate.conf`

### Phase 4 — Packaging (Week 3–4)

- [ ] `packaging/build_deb.sh`
- [ ] `packaging/postinstall.sh`, `packaging/preremove.sh`
- [ ] Build and test `.deb` install on clean Ubuntu VM
- [ ] `packaging/build_rpm.sh`
- [ ] Build and test `.rpm` on Fedora VM (or Docker)

### Phase 5 — Documentation & Demo (Week 4)

- [ ] `docs/design.md` — architecture, decisions, diagrams
- [ ] `docs/deploy.md` — build instructions, install walkthrough
- [ ] Demo recording (asciinema or video)
- [ ] Final review: README accuracy, test coverage ≥ 80%

---

## 10. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `inotify` limit too low on test system | Medium | `sysctl fs.inotify.max_user_watches=524288` |
| `fpm` version incompatibilities | Low | Pin Ruby gem version in build script |
| `psutil` disk I/O unavailable in container | Medium | Catch `NotImplementedError`, return `{}` gracefully |
| syslog socket path differs by distro | Medium | Make `syslog_address` configurable in YAML |
| Service fails if log dir missing | Low | `postinstall.sh` creates `/var/log/monitoring-agent/` |
