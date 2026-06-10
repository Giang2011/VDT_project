import psutil


def collect() -> dict:
    try:
        counters = psutil.net_io_counters(pernic=False)
    except AttributeError:
        return {}

    if counters is None:
        return {}

    return {
        "net_bytes_sent": counters.bytes_sent,
        "net_bytes_recv": counters.bytes_recv,
        "net_packets_sent": counters.packets_sent,
        "net_packets_recv": counters.packets_recv,
    }
