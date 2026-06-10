import psutil


def collect() -> dict:
    vm = psutil.virtual_memory()
    return {
        "mem_total_mb": round(vm.total / 1024**2, 1),
        "mem_used_mb": round(vm.used / 1024**2, 1),
        "mem_free_mb": round(vm.free / 1024**2, 1),
        "mem_percent": vm.percent,
    }
