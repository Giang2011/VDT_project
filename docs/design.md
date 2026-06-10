# Design Document — System Monitoring Agent

## 1. System Overview

`monitoring-agent` is a Linux background service that periodically collects host health metrics, watches selected files or directories for filesystem activity, and writes structured logs locally and optionally to syslog. The goal of the project is to provide a lightweight, installable monitoring daemon suitable for a university or lab environment. Its scope is intentionally small: it focuses on local observability for CPU, memory, disk, network, and file change events rather than remote aggregation, dashboards, or alert delivery integrations.

The agent is designed to run under `systemd`, start automatically on boot, and recover automatically from failures. Configuration is provided through a YAML file so that the service can be deployed consistently across development and target Linux systems.

## 2. Architecture Diagram

```text
+--------------------------------------------------------------+
|                    monitoring-agent service                   |
|                                                              |
|  +------------------+                                        |
|  | YAML Config File  |                                        |
|  +---------+--------+                                        |
|            |                                                 |
|            v                                                 |
|  +------------------+     +------------------------------+   |
|  |   main.py        |---->|   Collector Modules           |   |
|  | startup + loop   |     | cpu / memory / disk / network |   |
|  +--------+---------+     +------------------------------+   |
|           |                                                     |
|           |             +----------------------------------+    |
|           +------------>|   fs_watcher.py                  |    |
|           |             | watchdog observer + handler      |    |
|           |             +----------------------------------+    |
|           |                                                     |
|           v                                                     |
|  +------------------+     +------------------------------+     |
|  |   alerter.py     |<----| collected metrics dictionary  |     |
|  | threshold checks  |     +------------------------------+     |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +------------------+                                            |
|  |   logger.py      |----> rotating log file                     |
|  | file + syslog    |----> optional syslog                       |
|  +------------------+                                            |
+--------------------------------------------------------------+
```

## 3. Component Descriptions

### `src/monitoring_agent/main.py`

This is the entry point for the service. It loads configuration, creates the logger, starts filesystem watchers, and enters the main collection loop. It also handles graceful shutdown on `SIGINT` and `SIGTERM` so the observer thread and process exit cleanly under `systemd`.

### `src/monitoring_agent/config.py`

This module loads the YAML configuration file and merges it with safe defaults. It validates important values such as collection intervals and threshold ranges, and it warns when watched paths do not exist. Centralizing validation here keeps the rest of the service simpler and reduces the risk of runtime errors caused by malformed configuration.

### `src/monitoring_agent/logger.py`

This module configures the application logger. It creates a `RotatingFileHandler` for persistent local logs and can optionally attach a `SysLogHandler` for integration with the system journal or local syslog daemon. The logging format is simple and consistent so that collected metrics, filesystem events, and warnings are easy to read.

### `src/monitoring_agent/collectors/*`

The collector modules isolate the platform-specific metric gathering logic. `cpu.py`, `memory.py`, `disk.py`, and `network.py` each return a flat dictionary of measurements. This design makes it easy to combine outputs, test collectors independently, and disable specific collectors through configuration when needed.

### `src/monitoring_agent/collectors/fs_watcher.py`

This module wraps `watchdog` to monitor filesystem paths and emit immediate log lines when files change. It runs alongside the periodic metric loop and provides event-driven visibility into directory activity. Because it uses `watchdog.Observer`, it can watch multiple paths concurrently with minimal custom threading logic.

### `src/monitoring_agent/alerter.py`

This module compares collected metrics against configured thresholds and logs warnings when values exceed acceptable limits. It does not send notifications externally in v1.0; instead, it provides a clear warning trail in the log output and journal. Keeping alerting logic separate from collection logic improves maintainability.

## 4. Data Flow

1. The service starts and reads `config.yaml`.
2. Configuration is validated and merged with defaults.
3. The logger is configured with file rotation and optional syslog output.
4. Filesystem watchers are started for all configured watch paths.
5. On each collection interval, enabled collectors gather metrics and merge them into one flat dictionary.
6. The metrics are formatted into a single log line.
7. Threshold checks run against the same metric dictionary and generate warnings when limits are exceeded.
8. Filesystem events are logged immediately whenever they occur.
9. On shutdown, the observer is stopped and the service exits cleanly.

## 5. Key Design Decisions and Rationale

### Python

Python was chosen because it is well suited to systems scripting and has mature libraries for process metrics and filesystem monitoring. `psutil` provides a straightforward API for CPU, memory, disk, and network statistics, while `watchdog` offers a high-level interface around Linux filesystem notifications. Python also keeps the implementation readable for a student project and simplifies packaging.

### YAML Configuration

YAML is used instead of INI because it supports nested structures and lists naturally. That is especially useful for `watch_paths`, collector toggles, and grouped logging settings. YAML also remains human-readable and easy to edit during deployment.

### `fpm` Packaging

`fpm` was selected for packaging because it can wrap the Python project, systemd unit file, config template, and maintainer scripts into `.deb` or `.rpm` artifacts with a single tool. This avoids writing separate packaging logic for Debian and Red Hat families and keeps the build process simple.

## 6. Known Limitations and Future Improvements

- The current alerting system only writes warnings to logs; future versions could send email, webhooks, or integrations with chat systems.
- Metrics are logged as text rather than exported in a structured format such as JSON or Prometheus exposition.
- The service is local-only and does not support multi-host aggregation.
- Collector behavior is limited to a fixed set of system metrics; more advanced process, GPU, or container-level metrics could be added later.
- Filesystem watching is focused on configured paths and does not automatically discover new directories.
- Error handling is intentionally simple for v1.0; future work could add retries, backoff, and richer health reporting.
