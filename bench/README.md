# Benchmark: bare metal vs passthrough guest

The same script runs on both sides. It measures GEMM throughput (FP32, FP16) and copy bandwidth (host↔device, and device memory), reporting the median of 3 runs.

```bash
# 1. On the host, with the MI210 on amdgpu (before starting the VM)
bench/run.sh baremetal          # -> bench/results/baremetal.json

# 2. Inside the guest, with ROCm + ROCm PyTorch installed
bench/run.sh guest              # -> bench/results/guest.json
# copy guest.json back into bench/results/ on the host (or commit it from the guest)

# 3. Anywhere (standard library only)
python3 bench/plot.py           # -> comparison.md + comparison-{light,dark}.svg
```

`comparison.md` has the raw numbers, a table of environments (kernel, HIP, PyTorch versions) and the chart. On GitHub, the chart follows the viewer's light or dark theme. To show it on the main README:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="bench/results/comparison-dark.svg">
  <img alt="Guest results as % of bare metal" src="bench/results/comparison-light.svg">
</picture>
```

Tips: keep the GPU otherwise idle, use the same ROCm and PyTorch versions on both sides, and run each side twice to make sure the numbers are stable. To watch the GPU while it runs, see [`monitoring/`](../monitoring/README.md).
