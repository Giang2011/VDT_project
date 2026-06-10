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
