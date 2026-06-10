import psutil


def _sanitize_mountpoint(mountpoint: str) -> str:
    if mountpoint == "/":
        return "root"
    return mountpoint.strip("/").replace("/", "_") or "root"


def collect() -> dict:
    metrics = {}
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        key = f"disk_{_sanitize_mountpoint(part.mountpoint)}_percent"
        metrics[key] = usage.percent

    counters = psutil.disk_io_counters()
    if counters is not None:
        metrics["disk_io_read_mb"] = round(counters.read_bytes / 1024**2, 1)
        metrics["disk_io_write_mb"] = round(counters.write_bytes / 1024**2, 1)

    return metrics
