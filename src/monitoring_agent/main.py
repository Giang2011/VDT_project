import argparse
import signal
import sys
import time

from monitoring_agent import alerter, config, logger
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
        if observer:
            observer.stop()
            observer.join(timeout=5)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    interval = cfg["agent"]["interval_seconds"]

    while True:
        try:
            metrics = collect_all(cfg)

            cpu_items = []
            memory_items = []
            disk_items = []
            network_items = []
            other_items = []

            for key, value in metrics.items():
                if key.startswith("cpu_"):
                    cpu_items.append(f"{key}={value}")
                elif key.startswith("mem_"):
                    memory_items.append(f"{key}={value}")
                elif key.startswith("disk_"):
                    disk_items.append(f"{key}={value}")
                elif key.startswith("net_"):
                    network_items.append(f"{key}={value}")
                else:
                    other_items.append(f"{key}={value}")

            if cpu_items:
                log.info(f"[CPU] {' '.join(cpu_items)}")
            if memory_items:
                log.info(f"[MEMORY] {' '.join(memory_items)}")
            if disk_items:
                log.info(f"[DISK] {' '.join(disk_items)}")
            if network_items:
                log.info(f"[NETWORK] {' '.join(network_items)}")
            if other_items:
                log.info(f"[METRICS] {' '.join(other_items)}")

            alerter.check(metrics, cfg.get("thresholds", {}), log)
        except Exception as exc:
            log.error(f"[AGENT] Collection error: {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
