import copy
import os
import warnings
from typing import Any

import yaml


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


class ConfigError(ValueError):
    pass


def _deep_merge(defaults: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(defaults)
    for key, value in values.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    cfg = _deep_merge(DEFAULTS, data)

    interval = cfg.get("agent", {}).get("interval_seconds", 60)
    if interval < 1:
        raise ConfigError("interval_seconds must be >= 1")

    for key in ("cpu_percent", "memory_percent", "disk_percent"):
        value = cfg.get("thresholds", {}).get(key)
        if value is not None and not 0 <= value <= 100:
            raise ConfigError(f"{key} must be between 0 and 100")

    for entry in cfg.get("watch_paths", []):
        path_to_check = entry.get("path", "")
        if path_to_check and not os.path.exists(path_to_check):
            warnings.warn(f"Watch path does not exist: {path_to_check}", stacklevel=2)

    return cfg
