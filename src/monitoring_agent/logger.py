import logging
import os
from logging.handlers import RotatingFileHandler, SysLogHandler


def setup(cfg: dict) -> logging.Logger:
    logger = logging.getLogger("monitoring_agent")
    logger.setLevel(getattr(logging, cfg.get("logging", {}).get("level", "INFO").upper(), logging.INFO))
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    log_cfg = cfg.get("logging", {})
    log_file = log_cfg.get("log_file", "/var/log/monitoring-agent/agent.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s")

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=log_cfg.get("max_bytes", 10_485_760),
        backupCount=log_cfg.get("backup_count", 5),
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if log_cfg.get("syslog", False):
        syslog_address = log_cfg.get("syslog_address", "/dev/log")
        syslog_handler = SysLogHandler(address=syslog_address, facility=SysLogHandler.LOG_DAEMON)
        syslog_handler.setFormatter(formatter)
        logger.addHandler(syslog_handler)

    return logger
