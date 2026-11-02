# ROCm-Passthrough-K3s

[![CI](https://github.com/xuej41/rocm-passthrough-k3s/actions/workflows/ci.yml/badge.svg)](https://github.com/xuej41/rocm-passthrough-k3s/actions/workflows/ci.yml)

Using my AMD Instinct MI210 (PCIe) passed through with VFIO to a KVM guest running ROCm, scheduled by k3s with AMD's device plugin. Also includes `passthrough-check`, a small tested tool that checks a GPU's passthrough readiness from sysfs.

```
Host (Ubuntu, amdgpu drives the RX 480 display)
 └─ vfio-pci ── MI210
     └─ KVM / QEMU q35 + OVMF (UEFI)
         └─ Ubuntu 22.04 guest ── ROCm
             ├─ k3s ── ROCm device plugin (amd.com/gpu)
             │   └─ pod: rocm-smi
             └─ AMD metrics exporter ── Prometheus ── Grafana
```

## Status

| Component | Status |
|---|---|
| Host: IOMMU, KVM, libvirt, OVMF | Planned |
| MI210 passthrough VM with ROCm, benchmarked against bare metal | Planned |
| k3s pod using `amd.com/gpu: 1` | Planned |
| `passthrough-check` tool, tests, CI | In progress |
| GPU monitoring: AMD exporter, Prometheus, Grafana | In progress |
| Docker GPU access (`/dev/kfd`, `/dev/dri`) | Done |
| NVIDIA path (RTX 4060 Ti) | Planned |

Errors and fixes: [LOG.md](LOG.md).

## Results

Bare metal vs guest: see [bench/results/comparison.md](bench/results/comparison.md) (not run yet). [`bench/`](bench/README.md) runs the same GEMM and copy-bandwidth tests on both sides, and `bench/plot.py` turns the results into a table and chart.

Live GPU metrics: [`monitoring/`](monitoring/README.md) sets up AMD's Device Metrics Exporter, Prometheus and a Grafana dashboard, on k3s or with Docker Compose.

## passthrough-check

Reads sysfs and reports, for each GPU:

- the bound **driver** (`amdgpu`, `vfio-pci`, …)
- its **IOMMU group** and the other devices in it (bridges and sibling functions are allowed)
- **PCIe link speed and width** compared with the maximum
- the **reset method**, which tells you whether the card can recover after the VM stops

```bash
pip install -e '.[dev]'
passthrough-check                                  # auto-detect AMD/NVIDIA GPUs
passthrough-check 0c:00.0 --expect-driver vfio-pci # while the VM runs
passthrough-check 0c:00.0 --expect-driver amdgpu   # after the VM stops
passthrough-check --json
```

Exit codes: `0` ready, `1` problems found, `2` device not found or bad input.

Development: `pytest`, then `ruff check . && ruff format --check .`. The tests build a fake sysfs tree, so they run anywhere, including CI.

## Repo layout

| Path | Purpose |
|---|---|
| `host/` | Host checks, IOMMU group listing, vfio-pci fallback config |
| `vm/` | VM creation and libvirt XML snippets |
| `k8s/` | GPU pod manifests (AMD, and optional NVIDIA) |
| `bench/` | Benchmark, results, and chart generator |
| `monitoring/` | Prometheus + Grafana + AMD exporter (k3s or Docker Compose), MI210 dashboard |
| `src/`, `tests/` | `passthrough-check` and its tests |
| `docs/` | Troubleshooting, AMD vs NVIDIA comparison, roadmap |

## Scope

- Passthrough, the k3s GPU pod, Docker GPU access, GPU monitoring.
- Future: see [docs/roadmap.md](docs/roadmap.md) (KubeVirt, SR-IOV/GIM, vLLM, packaging).