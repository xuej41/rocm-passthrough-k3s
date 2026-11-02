"""GPU benchmark: GEMM throughput and copy bandwidth, written as a JSON summary.

Run the same script on bare metal and inside the passthrough guest, then compare
the two JSON files with bench/plot.py. Needs ROCm PyTorch (torch.cuda maps to HIP).

    python3 bench/gpu_bench.py --label baremetal --out bench/results/baremetal.json
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone

try:
    import torch
except ImportError:
    sys.exit("torch not installed (install ROCm PyTorch)")

RUNS = 3  # each metric is measured RUNS times; the median is reported


def pick_device() -> torch.device:
    if not torch.cuda.is_available():
        sys.exit("no GPU visible to torch")
    names = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    # On the host the RX 480 may also be visible; prefer the Instinct card.
    idx = next((i for i, n in enumerate(names) if "MI" in n), 0)
    return torch.device(f"cuda:{idx}")


def timed(fn, iters: int, warmup: int = 3) -> float:
    """Seconds per call, averaged over iters, after warmup."""
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    t = time.perf_counter()
    for _ in range(iters):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t) / iters


def median_of(fn) -> float:
    return statistics.median(fn() for _ in range(RUNS))


def gemm_tflops(dev, dtype, n: int = 8192, iters: int = 50) -> float:
    a = torch.randn(n, n, device=dev, dtype=dtype)
    b = torch.randn(n, n, device=dev, dtype=dtype)
    return 2 * n**3 / timed(lambda: a @ b, iters) / 1e12


def copy_gbs(dev, kind: str, size_mib: int = 1024, iters: int = 20) -> float:
    n = size_mib * 2**20
    d1 = torch.empty(n, dtype=torch.uint8, device=dev)
    if kind == "d2d":
        d2 = torch.empty_like(d1)
        # a device-to-device copy reads n bytes and writes n bytes
        return 2 * n / timed(lambda: d2.copy_(d1), iters) / 1e9
    host = torch.empty(n, dtype=torch.uint8, pin_memory=True)
    if kind == "h2d":
        fn = lambda: d1.copy_(host, non_blocking=True)  # noqa: E731
    else:
        fn = lambda: host.copy_(d1, non_blocking=True)  # noqa: E731
    return n / timed(fn, iters) / 1e9


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--label", required=True, choices=["baremetal", "guest"])
    p.add_argument("--out", required=True, help="JSON file to write")
    args = p.parse_args()

    dev = pick_device()
    print("device:", torch.cuda.get_device_name(dev), flush=True)

    tests = [
        ("gemm_fp32", "GEMM FP32", "TFLOPS", lambda: gemm_tflops(dev, torch.float32)),
        ("gemm_fp16", "GEMM FP16", "TFLOPS", lambda: gemm_tflops(dev, torch.float16)),
        ("h2d", "Host → device copy", "GB/s", lambda: copy_gbs(dev, "h2d")),
        ("d2h", "Device → host copy", "GB/s", lambda: copy_gbs(dev, "d2h")),
        ("d2d", "Device memory copy", "GB/s", lambda: copy_gbs(dev, "d2d")),
    ]
    metrics = []
    for key, name, unit, fn in tests:
        value = median_of(fn)
        print(f"{name:22} {value:10.2f} {unit}", flush=True)
        metrics.append({"key": key, "name": name, "unit": unit, "value": round(value, 3)})

    summary = {
        "label": args.label,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": {
            "device": torch.cuda.get_device_name(dev),
            "kernel": platform.release(),
            "hip": getattr(torch.version, "hip", None),
            "torch": torch.__version__,
        },
        "metrics": metrics,
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
