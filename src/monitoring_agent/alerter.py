import logging


def check(metrics: dict, thresholds: dict, logger: logging.Logger) -> None:
    """Compare metrics against thresholds; emit WARNING when exceeded."""
    # Danh sách các chỉ số được so sánh với ngưỡng tương ứng.
    checks = [
        ("cpu_percent", thresholds.get("cpu_percent", 80), "CPU usage", "[CPU]"),
        ("mem_percent", thresholds.get("memory_percent", 85), "Memory usage", "[MEMORY]"),
    ]

    # Khi vượt ngưỡng, mọi cảnh báo đều bắt đầu bằng [ALERT] để đi vào alerts.log.
    # Sau đó mới thêm nhãn nguồn (CPU/MEMORY) để biết cảnh báo này thuộc phần nào.
    for key, limit, label, collector_tag in checks:
        value = metrics.get(key)
        if value is not None and value > limit:
            logger.warning(f"[ALERT] {collector_tag} {label} {value:.1f}% exceeds threshold {limit}%")

    # Kiểm tra từng partition/mount của disk và cảnh báo nếu vượt ngưỡng.
    disk_limit = thresholds.get("disk_percent", 90)
    for k, v in metrics.items():
        if k.startswith("disk_") and k.endswith("_percent"):
            if v > disk_limit:
                mount = k.replace("disk_", "").replace("_percent", "")
                logger.warning(f"[ALERT] [DISK] Disk ({mount}) {v:.1f}% exceeds threshold {disk_limit}%")
