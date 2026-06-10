from . import cpu, disk, memory, network


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
