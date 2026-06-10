from logging.handlers import RotatingFileHandler, SysLogHandler

from monitoring_agent.logger import setup


def _base_cfg(log_file, syslog=False):
    return {
        "logging": {
            "log_file": str(log_file),
            "max_bytes": 1024,
            "backup_count": 3,
            "syslog": syslog,
            "syslog_address": "/dev/log",
            "level": "INFO",
        }
    }


def test_file_handler_created(tmp_path):
    cfg = _base_cfg(tmp_path / "logs" / "agent.log")

    logger = setup(cfg)

    assert any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers)


def test_syslog_handler_added_when_enabled(tmp_path):
    cfg = _base_cfg(tmp_path / "agent.log", syslog=True)

    logger = setup(cfg)

    assert any(isinstance(handler, SysLogHandler) for handler in logger.handlers)


def test_no_syslog_when_disabled(tmp_path):
    cfg = _base_cfg(tmp_path / "agent.log", syslog=False)

    logger = setup(cfg)

    assert not any(isinstance(handler, SysLogHandler) for handler in logger.handlers)


def test_log_dir_created(tmp_path):
    log_dir = tmp_path / "nested" / "logs"
    cfg = _base_cfg(log_dir / "agent.log")

    setup(cfg)

    assert log_dir.exists()
