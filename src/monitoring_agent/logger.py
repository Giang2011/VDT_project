import logging
import os
from logging.handlers import RotatingFileHandler, SysLogHandler


class PrefixFilter(logging.Filter):
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().startswith(self.prefix)


def _build_handler(log_file: str, max_bytes: int, backup_count: int, formatter: logging.Formatter, prefix: str | None = None) -> RotatingFileHandler:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = RotatingFileHandler(filename=log_file, maxBytes=max_bytes, backupCount=backup_count)
    handler.setFormatter(formatter)
    if prefix:
        handler.addFilter(PrefixFilter(prefix))
    return handler


def setup(cfg: dict) -> logging.Logger:
    logger = logging.getLogger("monitoring_agent")
    logger.setLevel(getattr(logging, cfg.get("logging", {}).get("level", "INFO").upper(), logging.INFO))
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    log_cfg = cfg.get("logging", {})
    formatter = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s")
    max_bytes = log_cfg.get("max_bytes", 10_485_760)
    backup_count = log_cfg.get("backup_count", 5)

    base_log = log_cfg.get("log_file", "/var/log/monitoring-agent/agent.log")
    logger.addHandler(_build_handler(base_log, max_bytes, backup_count, formatter))

    per_collector = log_cfg.get("collector_logs", {})
    for name in ("cpu", "memory", "disk", "network", "alerts", "fs"):
        cfg_item = per_collector.get(name, {})
        if not cfg_item.get("enabled", True):
            continue
        logger.addHandler(
            _build_handler(
                cfg_item.get("log_file", f"/var/log/monitoring-agent/{name}/{name}.log"),
                cfg_item.get("max_bytes", max_bytes),
                cfg_item.get("backup_count", backup_count),
                formatter,
                prefix=f"[{name.upper()}]",
            )
        )

    if log_cfg.get("syslog", False):
        syslog_address = log_cfg.get("syslog_address", "/dev/log")
        syslog_handler = SysLogHandler(address=syslog_address, facility=SysLogHandler.LOG_DAEMON)
        syslog_handler.setFormatter(formatter)
        logger.addHandler(syslog_handler)

    return logger
