import logging


def check(metrics: dict, thresholds: dict, logger: logging.Logger) -> None:
    """Compare metrics against thresholds; emit WARNING when exceeded."""
    checks = [
        ("cpu_percent", thresholds.get("cpu_percent", 80), "CPU usage", "[ALERT] [CPU]"),
        ("mem_percent", thresholds.get("memory_percent", 85), "Memory usage", "[ALERT] [MEMORY]"),
    ]
    for key, limit, label, prefix in checks:
        value = metrics.get(key)
        if value is not None and value > limit:
            logger.warning(f"{prefix} {label} {value:.1f}% exceeds threshold {limit}%")

    disk_limit = thresholds.get("disk_percent", 90)
    for k, v in metrics.items():
        if k.startswith("disk_") and k.endswith("_percent"):
            if v > disk_limit:
                mount = k.replace("disk_", "").replace("_percent", "")
                logger.warning(f"[ALERT] [DISK] Disk ({mount}) {v:.1f}% exceeds threshold {disk_limit}%")
