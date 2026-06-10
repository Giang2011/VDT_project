from unittest.mock import patch

from monitoring_agent.collectors import collect_all
from monitoring_agent.collectors import cpu, disk, memory, network


def test_cpu_collect_keys(mock_psutil):
    result = cpu.collect()

    assert "cpu_percent" in result
    assert "cpu_count" in result
    assert "load_avg_1m" in result


def test_memory_collect_keys(mock_psutil):
    result = memory.collect()

    assert "mem_total_mb" in result
    assert "mem_percent" in result


def test_disk_collect_keys(mock_psutil):
    result = disk.collect()

    assert any(key.startswith("disk_") and key.endswith("_percent") for key in result)


def test_network_collect_keys(mock_psutil):
    result = network.collect()

    assert "net_bytes_sent" in result
    assert "net_bytes_recv" in result


def test_collect_all_respects_cfg(mock_psutil):
    cfg = {
        "collectors": {
            "cpu": False,
            "memory": True,
            "disk": True,
            "network": True,
        }
    }

    with patch("monitoring_agent.collectors.cpu.collect", return_value={"cpu_percent": 1}), \
        patch("monitoring_agent.collectors.memory.collect", return_value={"mem_percent": 1}), \
        patch("monitoring_agent.collectors.disk.collect", return_value={"disk_root_percent": 1}), \
        patch("monitoring_agent.collectors.network.collect", return_value={"net_bytes_sent": 1}):
        result = collect_all(cfg)

    assert not any(key.startswith("cpu_") for key in result)
    assert "mem_percent" in result
    assert "disk_root_percent" in result
    assert "net_bytes_sent" in result
