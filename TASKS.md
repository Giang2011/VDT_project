# ✅ TASKS — System Monitoring Agent

> **Agent instructions:**
> - Work through tasks **in order** within each phase. Later tasks may depend on earlier ones.
> - All files MUST be created at the exact paths defined in `STRUCTURE.md`. Do not improvise paths.
> - After completing each task, mark it `[x]`.
> - If a task generates a file, confirm the file exists at the specified path before marking done.
> - Do not skip `# STRUCTURE NOTE` comments — they enforce `STRUCTURE.md` compliance.

---

## Phase 1 — Project Scaffold & Core Collectors

### TASK-01 — Initialize project root files

Create the following files in the **project root** (not in `src/`):

- [x] **`pyproject.toml`** at `monitoring-agent/pyproject.toml`

  ```toml
  [build-system]
  requires = ["setuptools>=67", "wheel"]
  build-backend = "setuptools.backends.legacy:build"

  [project]
  name = "monitoring-agent"
  version = "1.0.0"
  description = "Linux system monitoring background service"
  requires-python = ">=3.10"
  dependencies = [
      "psutil>=5.9.0",
      "watchdog>=3.0.0",
      "PyYAML>=6.0",
      "APScheduler>=3.10.0",
  ]

  [project.scripts]
  monitoring-agent = "monitoring_agent.main:main"

  [tool.setuptools.packages.find]
  where = ["src"]
  ```

- [x] **`setup.py`** at `monitoring-agent/setup.py`

  ```python
  from setuptools import setup
  setup()
  ```

- [x] **`requirements.txt`** at `monitoring-agent/requirements.txt`

  ```
  psutil>=5.9.0
  watchdog>=3.0.0
  PyYAML>=6.0
  APScheduler>=3.10.0
  ```

- [x] **`requirements-dev.txt`** at `monitoring-agent/requirements-dev.txt`

  ```
  pytest>=7.0
  pytest-cov>=4.0
  flake8>=6.0
  black>=23.0
  ```

- [x] **`.gitignore`** at `monitoring-agent/.gitignore`

  ```
  .venv/
  __pycache__/
  *.pyc
  *.egg-info/
  dist/
  build/
  .coverage
  htmlcov/
  ```

- [x] **`.flake8`** at `monitoring-agent/.flake8`

  ```ini
  [flake8]
  max-line-length = 100
  exclude = .venv,build,dist
  ```

> # STRUCTURE NOTE: All files above go in project root `monitoring-agent/` — NOT in `src/`.

---

### TASK-02 — Create Python package skeleton

Create the following **empty or minimal** files to establish the package structure.
All paths are relative to project root.

- [x] `src/monitoring_agent/__init__.py`

  ```python
  __version__ = "1.0.0"
  ```

- [x] `src/monitoring_agent/collectors/__init__.py`

  Leave empty for now (populated in TASK-07).

- [x] `tests/__init__.py` — empty file

> # STRUCTURE NOTE:
> - Source lives under `src/monitoring_agent/` (NOT `monitoring_agent/` at root)
> - Collector sub-package lives under `src/monitoring_agent/collectors/`
> - Tests live under `tests/` at project root

---

### TASK-03 — Implement `config.py`

**File:** `src/monitoring_agent/config.py`

Implement a `load(path: str) -> dict` function that:

1. Opens and parses the YAML file at `path`
2. Merges parsed values with the following defaults (missing keys get defaults, present keys override):
   ```python
   DEFAULTS = {
       "agent": {"interval_seconds": 60},
       "collectors": {"cpu": True, "memory": True, "disk": True, "network": True},
       "watch_paths": [],
       "thresholds": {"cpu_percent": 80, "memory_percent": 85, "disk_percent": 90},
       "logging": {
           "log_file": "/var/log/monitoring-agent/agent.log",
           "max_bytes": 10_485_760,
           "backup_count": 5,
           "syslog": False,
           "syslog_address": "/dev/log",
           "level": "INFO",
       },
   }
   ```
3. Raises `ConfigError(ValueError)` if:
   - Any threshold value is not in 0–100
   - `interval_seconds` is < 1
4. Logs a `WARNING` (using stdlib `warnings.warn`) if a `watch_paths` entry `path` does not exist on disk

Also define `class ConfigError(ValueError): pass`

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/config.py`

---

### TASK-04 — Implement `logger.py`

**File:** `src/monitoring_agent/logger.py`

Implement `setup(cfg: dict) -> logging.Logger`:

1. Creates a logger named `"monitoring_agent"`
2. Sets level from `cfg["logging"]["level"]` (e.g. `"INFO"` → `logging.INFO`)
3. Adds a `RotatingFileHandler`:
   - filename: `cfg["logging"]["log_file"]`
   - maxBytes: `cfg["logging"]["max_bytes"]`
   - backupCount: `cfg["logging"]["backup_count"]`
   - Creates parent directory if it does not exist (`os.makedirs(..., exist_ok=True)`)
4. If `cfg["logging"]["syslog"]` is `True`, adds a `SysLogHandler`:
   - address: `cfg["logging"]["syslog_address"]` (string path like `/dev/log` or tuple `("host", 514)`)
   - facility: `logging.handlers.SysLogHandler.LOG_DAEMON`
5. Both handlers use formatter: `"%(asctime)s %(levelname)-5s %(message)s"`
6. Returns the configured logger

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/logger.py`

---

### TASK-05 — Implement `collectors/cpu.py`

**File:** `src/monitoring_agent/collectors/cpu.py`

Implement `collect() -> dict`:

```python
import psutil

def collect() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_count": psutil.cpu_count(logical=True),
        "load_avg_1m": psutil.getloadavg()[0],
        "load_avg_5m": psutil.getloadavg()[1],
        "load_avg_15m": psutil.getloadavg()[2],
    }
```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/collectors/cpu.py`

---

### TASK-06 — Implement `collectors/memory.py`

**File:** `src/monitoring_agent/collectors/memory.py`

Implement `collect() -> dict`:

```python
import psutil

def collect() -> dict:
    vm = psutil.virtual_memory()
    return {
        "mem_total_mb": round(vm.total / 1024**2, 1),
        "mem_used_mb":  round(vm.used  / 1024**2, 1),
        "mem_free_mb":  round(vm.free  / 1024**2, 1),
        "mem_percent":  vm.percent,
    }
```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/collectors/memory.py`

---

### TASK-07 — Implement `collectors/disk.py`

**File:** `src/monitoring_agent/collectors/disk.py`

Implement `collect() -> dict`:

1. Iterate `psutil.disk_partitions(all=False)`
2. For each partition call `psutil.disk_usage(part.mountpoint)` — skip on `PermissionError`
3. Store as `disk_<mountpoint_sanitised>_percent` (replace `/` with `_root`, other `/` with `_`)
4. Also call `psutil.disk_io_counters()` — if `None` (e.g. inside Docker), skip gracefully
5. Return a flat dict, e.g.:
   ```python
   {
       "disk_root_percent": 45.3,
       "disk_boot_percent": 12.1,
       "disk_io_read_mb": 1024.0,
       "disk_io_write_mb": 512.0,
   }
   ```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/collectors/disk.py`

---

### TASK-08 — Implement `collectors/network.py`

**File:** `src/monitoring_agent/collectors/network.py`

Implement `collect() -> dict`:

1. Call `psutil.net_io_counters(pernic=False)` for aggregate stats
2. Return:
   ```python
   {
       "net_bytes_sent":    counters.bytes_sent,
       "net_bytes_recv":    counters.bytes_recv,
       "net_packets_sent":  counters.packets_sent,
       "net_packets_recv":  counters.packets_recv,
   }
   ```
3. Handle `AttributeError` gracefully (return empty dict if unavailable)

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/collectors/network.py`

---

### TASK-09 — Implement `collectors/__init__.py` — `collect_all()`

**File:** `src/monitoring_agent/collectors/__init__.py`

```python
from . import cpu, memory, disk, network

def collect_all(cfg: dict) -> dict:
    """Call each enabled collector and merge results into one flat dict."""
    metrics = {}
    c = cfg.get("collectors", {})
    if c.get("cpu", True):
        metrics.update(cpu.collect())
    if c.get("memory", True):
        metrics.update(memory.collect())
    if c.get("disk", True):
        metrics.update(disk.collect())
    if c.get("network", True):
        metrics.update(network.collect())
    return metrics
```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/collectors/__init__.py`

---

### TASK-10 — Implement `collectors/fs_watcher.py`

**File:** `src/monitoring_agent/collectors/fs_watcher.py`

Implement `AgentFSHandler` and `start_watchers`:

```python
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AgentFSHandler(FileSystemEventHandler):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger

    def on_any_event(self, event):
        if not event.is_directory:
            self.logger.info(f"[FS] {event.event_type.upper()} {event.src_path}")

def start_watchers(watch_paths: list, logger: logging.Logger) -> Observer:
    """
    Schedule a handler for each configured path.
    Returns a started Observer thread.
    """
    observer = Observer()
    for entry in watch_paths:
        path = entry.get("path", "")
        recursive = entry.get("recursive", False)
        handler = AgentFSHandler(logger)
        observer.schedule(handler, path, recursive=recursive)
        logger.info(f"[WATCHER] Watching: {path} (recursive={recursive})")
    observer.start()
    return observer
```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/collectors/fs_watcher.py`

---

### TASK-11 — Implement `alerter.py`

**File:** `src/monitoring_agent/alerter.py`

```python
import logging

def check(metrics: dict, thresholds: dict, logger: logging.Logger) -> None:
    """Compare metrics against thresholds; emit WARNING when exceeded."""
    checks = [
        ("cpu_percent",   thresholds.get("cpu_percent", 80),    "CPU usage"),
        ("mem_percent",   thresholds.get("memory_percent", 85), "Memory usage"),
    ]
    for key, limit, label in checks:
        value = metrics.get(key)
        if value is not None and value > limit:
            logger.warning(f"[ALERT] {label} {value:.1f}% exceeds threshold {limit}%")

    # Disk: check all disk_*_percent keys
    disk_limit = thresholds.get("disk_percent", 90)
    for k, v in metrics.items():
        if k.startswith("disk_") and k.endswith("_percent"):
            if v > disk_limit:
                mount = k.replace("disk_", "").replace("_percent", "")
                logger.warning(f"[ALERT] Disk ({mount}) {v:.1f}% exceeds threshold {disk_limit}%")
```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/alerter.py`

---

### TASK-12 — Implement `main.py`

**File:** `src/monitoring_agent/main.py`

Implement the full entry point:

```python
import argparse
import signal
import sys
import time

from monitoring_agent import config, logger, alerter
from monitoring_agent.collectors import collect_all
from monitoring_agent.collectors import fs_watcher


def main():
    parser = argparse.ArgumentParser(description="System Monitoring Agent")
    parser.add_argument(
        "--config", default="/etc/monitoring-agent/config.yaml",
        help="Path to config YAML file"
    )
    args = parser.parse_args()

    cfg = config.load(args.config)
    log = logger.setup(cfg)

    log.info("[AGENT] Starting monitoring-agent v1.0.0")

    observer = fs_watcher.start_watchers(cfg.get("watch_paths", []), log)

    def shutdown(sig, frame):
        log.info("[AGENT] Shutting down...")
        observer.stop()
        observer.join()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    interval = cfg["agent"]["interval_seconds"]

    while True:
        try:
            metrics = collect_all(cfg)
            metric_str = " ".join(f"{k}={v}" for k, v in metrics.items())
            log.info(f"[METRICS] {metric_str}")
            alerter.check(metrics, cfg.get("thresholds", {}), log)
        except Exception as exc:
            log.error(f"[AGENT] Collection error: {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
```

> # STRUCTURE NOTE: File path must be exactly `src/monitoring_agent/main.py`

---

## Phase 2 — Configuration File & Logrotate

### TASK-13 — Create `config/config.yaml.example`

- [x] **File:** `config/config.yaml.example`

Write the fully-commented YAML reference config (see Section 3 of `PLAN.md` for the full template).
Include inline comments explaining every key.

> # STRUCTURE NOTE: Config templates live in `config/` at project root, NOT in `src/`

---

### TASK-14 — Create `config/logrotate.conf`

- [x] **File:** `config/logrotate.conf`

```
/var/log/monitoring-agent/agent.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    postrotate
        systemctl kill -s HUP monitoring-agent.service > /dev/null 2>&1 || true
    endscript
}
```

> # STRUCTURE NOTE: File path must be exactly `config/logrotate.conf`

---

## Phase 3 — systemd Unit File

### TASK-15 — Create `systemd/monitoring-agent.service`

- [x] **File:** `systemd/monitoring-agent.service`

```ini
[Unit]
Description=System Monitoring Agent
Documentation=https://github.com/yourname/monitoring-agent
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

> # STRUCTURE NOTE: File path must be exactly `systemd/monitoring-agent.service`
> Do NOT place this file in `src/` or `config/`

---

## Phase 4 — Packaging Scripts

### TASK-16 — Create `packaging/postinstall.sh`

- [x] **File:** `packaging/postinstall.sh`

```bash
#!/bin/bash
set -e
systemctl daemon-reload
systemctl enable monitoring-agent
mkdir -p /var/log/monitoring-agent
echo "monitoring-agent installed. Start with: systemctl start monitoring-agent"
```

> # STRUCTURE NOTE: All packaging scripts live in `packaging/` — NOT in project root

---

### TASK-17 — Create `packaging/preremove.sh`

**File:** `packaging/preremove.sh`

```bash
#!/bin/bash
systemctl stop monitoring-agent  || true
systemctl disable monitoring-agent || true
```

---

### TASK-18 — Create `packaging/build_deb.sh`

**File:** `packaging/build_deb.sh`

Write the full `fpm` invocation as documented in `PLAN.md` Section 7.2.
Include:
- `set -e` at top
- `VERSION` variable
- `pip install --target=./build/lib .` step
- `fpm -s dir -t deb ...` command with all options
- Output to `../dist/` directory

> # STRUCTURE NOTE: Script lives at `packaging/build_deb.sh`
> Output packages must go to `dist/` (project root level), not inside `packaging/`

---

### TASK-19 — Create `packaging/build_rpm.sh`

**File:** `packaging/build_rpm.sh`

Mirror of `build_deb.sh` with `-t rpm` and `.rpm` output filename.

> # STRUCTURE NOTE: Script lives at `packaging/build_rpm.sh`

---

## Phase 5 — Tests

### TASK-20 — Create `tests/conftest.py`

**File:** `tests/conftest.py`

Define shared pytest fixtures:
- `tmp_config(tmp_path)` — writes a minimal `config.yaml` to a temp dir, returns its path
- `mock_psutil` — patches `psutil.cpu_percent`, `psutil.virtual_memory`, etc. with fixed values

> # STRUCTURE NOTE: Test files live in `tests/` at project root

---

### TASK-21 — Create `tests/test_config.py`

**File:** `tests/test_config.py`

Write tests:
- `test_load_valid_config` — loads `tmp_config`, asserts expected keys present
- `test_missing_keys_get_defaults` — minimal YAML, assert `interval_seconds == 60`
- `test_invalid_threshold_raises` — threshold > 100 raises `ConfigError`
- `test_invalid_interval_raises` — `interval_seconds: 0` raises `ConfigError`

---

### TASK-22 — Create `tests/test_collectors.py`

**File:** `tests/test_collectors.py`

Write tests for each collector using `unittest.mock.patch`:
- `test_cpu_collect_keys` — assert `cpu_percent`, `cpu_count`, `load_avg_1m` in result
- `test_memory_collect_keys` — assert `mem_total_mb`, `mem_percent` in result
- `test_disk_collect_keys` — assert at least one `disk_*_percent` key in result
- `test_network_collect_keys` — assert `net_bytes_sent`, `net_bytes_recv` in result
- `test_collect_all_respects_cfg` — disable cpu in cfg, assert no `cpu_*` keys in result

---

### TASK-23 — Create `tests/test_alerter.py`

**File:** `tests/test_alerter.py`

Write tests:
- `test_no_alert_below_threshold` — metrics all under limit, assert no `logger.warning` calls
- `test_cpu_alert_above_threshold` — `cpu_percent=90`, threshold=80, assert warning logged
- `test_disk_alert_above_threshold` — `disk_root_percent=95`, threshold=90, assert warning logged
- `test_multiple_alerts` — both CPU and disk exceeded, assert two warnings

---

### TASK-24 — Create `tests/test_logger.py`

**File:** `tests/test_logger.py`

Write tests:
- `test_file_handler_created` — after `setup()`, logger has a `RotatingFileHandler`
- `test_syslog_handler_added_when_enabled` — cfg with `syslog: true`, assert `SysLogHandler` present
- `test_no_syslog_when_disabled` — cfg with `syslog: false`, assert no `SysLogHandler`
- `test_log_dir_created` — non-existent log dir, assert `setup()` creates it

---

### TASK-25 — Create `tests/test_fs_watcher.py`

**File:** `tests/test_fs_watcher.py`

Write tests:
- `test_watcher_starts` — call `start_watchers` with a real `tmp_path`, assert `observer.is_alive()`
- `test_event_logged_on_file_write` — write a file to watched directory, assert logger.info called
  - Use `pytest`'s `tmp_path` fixture for the watched directory
  - Give watchdog ~0.5s to detect the event before asserting
- Teardown: always call `observer.stop()` + `observer.join()` in fixture cleanup

---

## Phase 6 — Documentation

### TASK-26 — Create `docs/design.md`

**File:** `docs/design.md`

Write a design document covering:
1. System overview (purpose, scope)
2. Architecture diagram (ASCII or description)
3. Component descriptions (one paragraph each)
4. Data flow description
5. Key design decisions and rationale (Python choice, YAML config, fpm packaging)
6. Known limitations and future improvements

---

### TASK-27 — Create `docs/deploy.md`

**File:** `docs/deploy.md`

Write a deployment guide covering:
1. Prerequisites (OS, Python version, fpm install)
2. Building `.deb` package step-by-step
3. Installing and verifying on Debian/Ubuntu
4. Building `.rpm` package step-by-step
5. Installing and verifying on RHEL/Fedora
6. Manual dev run instructions
7. Demo checklist (what to show in demo video)

---

## Summary Checklist

| Phase | Tasks | Status |
|---|---|---|
| 1 — Scaffold & Collectors | TASK-01 → TASK-12 | ⬜ Not started |
| 2 — Config & Logrotate | TASK-13 → TASK-14 | ⬜ Not started |
| 3 — systemd | TASK-15 | ⬜ Not started |
| 4 — Packaging | TASK-16 → TASK-19 | ⬜ Not started |
| 5 — Tests | TASK-20 → TASK-25 | ⬜ Not started |
| 6 — Docs | TASK-26 → TASK-27 | ⬜ Not started |

**Total: 27 tasks**
