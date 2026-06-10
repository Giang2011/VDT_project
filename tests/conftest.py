from collections import namedtuple

import psutil
import pytest


@pytest.fixture

def tmp_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """agent:\n  interval_seconds: 5\ncollectors:\n  cpu: true\n  memory: true\n  disk: true\n  network: true\nwatch_paths: []\nthresholds:\n  cpu_percent: 80\n  memory_percent: 85\n  disk_percent: 90\nlogging:\n  log_file: /tmp/monitoring-agent.log\n  max_bytes: 10485760\n  backup_count: 5\n  syslog: false\n  syslog_address: /dev/log\n  level: INFO\n""",
        encoding="utf-8",
    )
    return str(config_path)


@pytest.fixture

def mock_psutil(monkeypatch):
    vm = namedtuple("vm", "total used free percent")(
        total=8 * 1024**3,
        used=3 * 1024**3,
        free=5 * 1024**3,
        percent=37.5,
    )
    disk = namedtuple("disk", "read_bytes write_bytes")(
        read_bytes=1024 * 1024,
        write_bytes=512 * 1024,
    )
    counters = namedtuple("net", "bytes_sent bytes_recv packets_sent packets_recv")(
        bytes_sent=123456,
        bytes_recv=654321,
        packets_sent=100,
        packets_recv=200,
    )
    partition = namedtuple("partition", "device mountpoint fstype opts")(
        device="/dev/sda1",
        mountpoint="/",
        fstype="ext4",
        opts="rw",
    )
    usage = namedtuple("usage", "total used free percent")(
        total=100,
        used=45,
        free=55,
        percent=45.0,
    )

    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=1: 12.5)
    monkeypatch.setattr(psutil, "cpu_count", lambda logical=True: 8)
    monkeypatch.setattr(psutil, "getloadavg", lambda: (0.1, 0.2, 0.3))
    monkeypatch.setattr(psutil, "virtual_memory", lambda: vm)
    monkeypatch.setattr(psutil, "disk_io_counters", lambda: disk)
    monkeypatch.setattr(psutil, "net_io_counters", lambda pernic=False: counters)
    monkeypatch.setattr(psutil, "disk_partitions", lambda all=False: [partition])
    monkeypatch.setattr(psutil, "disk_usage", lambda mountpoint: usage)

    return {
        "virtual_memory": vm,
        "disk_io_counters": disk,
        "net_io_counters": counters,
        "disk_partitions": [partition],
        "disk_usage": usage,
    }
