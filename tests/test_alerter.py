from unittest.mock import MagicMock

from monitoring_agent.alerter import check


def test_no_alert_below_threshold():
    logger = MagicMock()
    metrics = {
        "cpu_percent": 20,
        "mem_percent": 30,
        "disk_root_percent": 40,
    }
    thresholds = {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
    }

    check(metrics, thresholds, logger)

    logger.warning.assert_not_called()


def test_cpu_alert_above_threshold():
    logger = MagicMock()
    metrics = {"cpu_percent": 90}
    thresholds = {"cpu_percent": 80}

    check(metrics, thresholds, logger)

    logger.warning.assert_called_once()
    assert "CPU usage" in logger.warning.call_args[0][0]


def test_disk_alert_above_threshold():
    logger = MagicMock()
    metrics = {"disk_root_percent": 95}
    thresholds = {"disk_percent": 90}

    check(metrics, thresholds, logger)

    logger.warning.assert_called_once()
    assert "Disk (root)" in logger.warning.call_args[0][0]


def test_multiple_alerts():
    logger = MagicMock()
    metrics = {
        "cpu_percent": 90,
        "disk_root_percent": 95,
    }
    thresholds = {
        "cpu_percent": 80,
        "disk_percent": 90,
    }

    check(metrics, thresholds, logger)

    assert logger.warning.call_count == 2
