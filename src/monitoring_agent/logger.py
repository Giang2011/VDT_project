import logging
import os
from logging.handlers import RotatingFileHandler, SysLogHandler


# Bộ lọc chỉ cho phép các message bắt đầu bằng một prefix cụ thể đi vào file handler.
class PrefixFilter(logging.Filter):
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().startswith(self.prefix)


# Bộ lọc loại bỏ các message có prefix thuộc danh sách đã tách riêng.
# Mục đích: agent.log chỉ giữ lại log không thuộc cpu/memory/disk/network/alerts/fs.
class ExcludePrefixesFilter(logging.Filter):
    def __init__(self, prefixes: tuple[str, ...]):
        super().__init__()
        self.prefixes = prefixes

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(message.startswith(prefix) for prefix in self.prefixes)


# Tạo một file handler có rotation theo dung lượng và gắn filter prefix nếu cần.
def _build_handler(log_file: str, max_bytes: int, backup_count: int, formatter: logging.Formatter, prefix: str | None = None) -> RotatingFileHandler:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = RotatingFileHandler(filename=log_file, maxBytes=max_bytes, backupCount=backup_count)
    handler.setFormatter(formatter)
    if prefix:
        handler.addFilter(PrefixFilter(prefix))
    return handler


# Khởi tạo logger chính của monitoring agent và gắn các file log riêng cho từng nhóm.
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

    # Các logger đã được tách riêng sẽ được gom vào đây để loại khỏi agent.log.
    per_collector = log_cfg.get("collector_logs", {})
    collector_prefixes = []
    for name in ("cpu", "memory", "disk", "network", "alerts", "fs"):
        cfg_item = per_collector.get(name, {})
        if not cfg_item.get("enabled", True):
            continue

        # Alert dùng prefix chung [ALERT] để toàn bộ cảnh báo đi vào alerts.log.
        if name == "alerts":
            prefix = "[ALERT]"
        else:
            prefix = f"[{name.upper()}]"

        # Prefix đầu dòng dùng để định tuyến đúng record sang file log tương ứng.
        collector_prefixes.append(prefix)
        logger.addHandler(
            _build_handler(
                cfg_item.get("log_file", f"/var/log/monitoring-agent/{name}/{name}.log"),
                cfg_item.get("max_bytes", max_bytes),
                cfg_item.get("backup_count", backup_count),
                formatter,
                prefix=prefix,
            )
        )

    # agent.log chỉ nhận các log không thuộc những nhóm đã tách riêng ở trên.
    base_log = log_cfg.get("log_file", "/var/log/monitoring-agent/agent.log")
    agent_handler = _build_handler(base_log, max_bytes, backup_count, formatter)
    if collector_prefixes:
        agent_handler.addFilter(ExcludePrefixesFilter(tuple(collector_prefixes)))
    logger.addHandler(agent_handler)

    # Gửi thêm sang syslog nếu hệ thống bật cấu hình này.
    if log_cfg.get("syslog", False):
        syslog_address = log_cfg.get("syslog_address", "/dev/log")
        syslog_handler = SysLogHandler(address=syslog_address, facility=SysLogHandler.LOG_DAEMON)
        syslog_handler.setFormatter(formatter)
        logger.addHandler(syslog_handler)

    return logger
