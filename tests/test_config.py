import pytest

from monitoring_agent.config import ConfigError, load


def test_load_valid_config(tmp_config):
    cfg = load(tmp_config)

    assert "agent" in cfg
    assert "collectors" in cfg
    assert "watch_paths" in cfg
    assert "thresholds" in cfg
    assert "logging" in cfg
    assert cfg["agent"]["interval_seconds"] == 5
    assert cfg["collectors"]["cpu"] is True


def test_missing_keys_get_defaults(tmp_path):
    config_path = tmp_path / "minimal.yaml"
    config_path.write_text("agent:\n  dummy: true\n", encoding="utf-8")

    cfg = load(str(config_path))

    assert cfg["agent"]["interval_seconds"] == 60
    assert cfg["collectors"]["cpu"] is True
    assert cfg["collectors"]["memory"] is True
    assert cfg["collectors"]["disk"] is True
    assert cfg["collectors"]["network"] is True


def test_invalid_threshold_raises(tmp_path):
    config_path = tmp_path / "invalid_threshold.yaml"
    config_path.write_text(
        """thresholds:\n  cpu_percent: 101\n""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load(str(config_path))


def test_invalid_interval_raises(tmp_path):
    config_path = tmp_path / "invalid_interval.yaml"
    config_path.write_text(
        """agent:\n  interval_seconds: 0\n""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load(str(config_path))
