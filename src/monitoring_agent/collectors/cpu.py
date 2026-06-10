import psutil


def collect() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_count": psutil.cpu_count(logical=True),
        "load_avg_1m": psutil.getloadavg()[0],
        "load_avg_5m": psutil.getloadavg()[1],
        "load_avg_15m": psutil.getloadavg()[2],
    }
