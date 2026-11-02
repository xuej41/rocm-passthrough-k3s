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

## Hardware

| Part | Model |
|---|---|
| GPU (compute) | AMD Instinct MI210 64 GB HBM2e with custom cooling shroud |
| GPU (host) | AMD Radeon RX 480 8 GB |
| CPU | AMD Ryzen 7 5800XT 8 core 16 thread CPU |
| Motherboard | ASUS ROG X570 Crosshair VIII Hero Wi-Fi|
| Memory | 32 GB (4 × 8 GB) Corsair Vengeance DDR4-3200 CL16 |
| Storage | Samsung 980 PRO |
| Power supply | Seasonic Prime Gold 1200 W |
| Chassis | Lian Li open-air test bench |

Host OS: Ubuntu 26.04 LTS, kernel 7.0.

<p align="center">
  <img src="docs/img/GPU.jpg" alt="AMD Instinct MI210 with a custom 3D-printed shroud and two fans on the end of the card" width="720">
  <br>
  <sub>The MI210 is passively cooled, so a 3D-printed shroud with two fans pushes air through its heatsink.</sub>
</p>
<p align="center">
  <img src="docs/img/main.jpg" alt="Open-air test bench with the MI210 and RX 480 installed" width="355">
  <img src="docs/img/topdown.jpg" alt="Top-down view: MI210 in the top PCIe slot, RX 480 below it" width="355">
  <br>
  <sub>The bench, and a top-down view: MI210 in the top slot, RX 480 below.</sub>
</p>

With both cards in, the board splits the CPU lanes x8/x8, so the MI210 runs at PCIe 4.0 x8.

## Status

| | |
|---|---|
| Host: IOMMU, KVM, libvirt, OVMF | Done |
| MI210 passthrough VM with ROCm, benchmarked against bare metal | Bare metal done, VM next |
| k3s pod using `amd.com/gpu: 1` | Planned |
| `passthrough-check` tool, tests, CI | Working |
| GPU monitoring: AMD exporter, Prometheus, Grafana | Configs written, not tried on the card yet |
| Docker GPU access (`/dev/kfd`, `/dev/dri`) | Done |
| NVIDIA path (RTX 4060 Ti) | Planned |

Problems I hit and how I got past them: [LOG.md](LOG.md).

## Results

[`bench/`](bench/) runs the same GEMM and copy tests on bare metal and in the guest, and `bench/plot.py` turns the two runs into [bench/results/comparison.md](bench/results/comparison.md).

## passthrough-check

Reads sysfs and, for each GPU, reports the bound driver, the IOMMU group and what else is in it, PCIe link speed and width against the max, and the reset method (whether the card can recover after the VM stops).

```bash
pip install -e '.[dev]'
passthrough-check                                  # every AMD/NVIDIA GPU
passthrough-check 0c:00.0 --expect-driver vfio-pci # while the VM runs
passthrough-check 0c:00.0 --expect-driver amdgpu   # after it stops
passthrough-check --json
```

Exits 0 if ready, 1 if it found a problem, 2 if the device doesn't exist. The tests build a fake sysfs tree, so `pytest` runs anywhere, CI included.

## License

MIT
