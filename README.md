# 🖥️ System Monitoring Agent

> A lightweight Linux background service that collects system metrics, watches filesystem events, and logs them periodically — packaged as a `.deb` / `.rpm` installer.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Build & Package](#build--package)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [License](#license)

---

## Overview

`monitoring-agent` is a Python-based daemon that runs as a `systemd` service on Linux. It periodically collects CPU, RAM, Disk, and Network statistics using `psutil`, watches specified files/directories for filesystem events using `watchdog`, and writes structured log entries to both a local log file and the system syslog.

The project is designed as a university-level systems programming exercise covering Linux services, Python packaging, and system observability fundamentals.

---

## Features

| Feature | Description |
|---|---|
| **CPU & RAM monitoring** | Usage percentage, load average, memory breakdown |
| **Disk monitoring** | Usage per partition, I/O read/write statistics |
| **Network monitoring** | Bytes sent/received, packet counts per interface |
| **Filesystem watcher** | inotify-based detection of create / modify / delete events on configured paths |
| **Periodic logging** | Structured log lines written to file at configurable intervals |
| **Syslog integration** | Forwards log entries to system syslog (`/dev/log`) |
| **Threshold alerting** | Emits WARN-level log when CPU/RAM/Disk exceeds configured thresholds |
| **systemd service** | Fully managed by systemd: auto-restart, journal integration |
| **Installable package** | Distributed as `.deb` (Debian/Ubuntu) and `.rpm` (RHEL/Fedora) |

---

## Requirements

### Runtime
- Linux (kernel ≥ 4.x, inotify support required)
- Python 3.10 or newer
- `systemd` (for service management)

### Python Dependencies
```
psutil>=5.9.0
watchdog>=3.0.0
PyYAML>=6.0
APScheduler>=3.10.0
```

### Build / Packaging Dependencies
- `fpm` (Effing Package Management) — requires Ruby `gem`
- `ruby` and `ruby-dev`
- `python3-setuptools`

---

## Installation

### Option A — Install from `.deb` package (Debian / Ubuntu)

```bash
sudo dpkg -i monitoring-agent_1.0.0_amd64.deb
sudo systemctl enable --now monitoring-agent
```

### Option B — Install from `.rpm` package (RHEL / Fedora / CentOS)

```bash
sudo rpm -ivh monitoring-agent-1.0.0.x86_64.rpm
sudo systemctl enable --now monitoring-agent
```

### Option C — Manual install (development)

```bash
git clone https://github.com/yourname/monitoring-agent.git
cd monitoring-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Configuration

The configuration file is located at `/etc/monitoring-agent/config.yaml` after installation.
During development, copy and edit the template:

```bash
cp config/config.yaml.example config/config.yaml
```

### `config.yaml` reference

```yaml
agent:
  interval_seconds: 30          # How often metrics are collected

collectors:
  cpu: true
  memory: true
  disk: true
  network: true

watch_paths:
  - path: /var/www/html
    recursive: true
    events: [created, modified, deleted]
  - path: /etc/nginx/nginx.conf
    recursive: false
    events: [modified]

thresholds:
  cpu_percent: 80
  memory_percent: 85
  disk_percent: 90

logging:
  log_file: /var/log/monitoring-agent/agent.log
  max_bytes: 10485760            # 10 MB before rotation
  backup_count: 5
  syslog: true
  syslog_address: /dev/log
  level: INFO
```

---

## Usage

### Service management

```bash
# Start / stop / restart
sudo systemctl start monitoring-agent
sudo systemctl stop monitoring-agent
sudo systemctl restart monitoring-agent

# Check status
sudo systemctl status monitoring-agent

# View live logs
sudo journalctl -u monitoring-agent -f

# View agent log file
tail -f /var/log/monitoring-agent/agent.log
```

### Running manually (for testing)

```bash
# Activate venv first if developing locally
source .venv/bin/activate
python -m monitoring_agent.main --config config/config.yaml
```

---

## Project Structure

```
monitoring-agent/
├── src/monitoring_agent/      # Core Python package
│   ├── collectors/            # Per-metric collector modules
│   ├── logger.py              # Logging setup (file + syslog)
│   ├── alerter.py             # Threshold checking
│   ├── config.py              # Config loader
│   └── main.py                # Entry point / main loop
├── config/                    # Default config templates
├── systemd/                   # systemd unit file
├── packaging/                 # Build scripts for .deb / .rpm
├── tests/                     # Unit tests
└── docs/                      # Design documentation
```

See [`STRUCTURE.md`](./STRUCTURE.md) for the full annotated directory tree.

---

## Build & Package

```bash
# Build .deb
bash packaging/build_deb.sh

# Build .rpm
bash packaging/build_rpm.sh
```

Output packages are written to `dist/`.
See [`PLAN.md`](./PLAN.md) for full build instructions and design rationale.

---

## Development Setup

```bash
# Clone repo
git clone https://github.com/yourname/monitoring-agent.git
cd monitoring-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run linter
flake8 src/

# Run formatter
black src/
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=monitoring_agent --cov-report=term-missing
```

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
