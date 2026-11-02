# Log

Things that broke and what fixed them

## Host↔Device copies only ~14 GB/s

Bare-metal bench gave 14.4 GB/s each way with pinned memory. PCIe 4.0 x16 should be closer to 25

`passthrough-check` said x16 at the GPU, but that's the link inside the card (the MI210 has its own PCIe switch). One level up, the slot is x8:

```
00:03.1 root port       16 GT/s x8  (max x8)
0a:00.0 MI210 upstream  16 GT/s x8  (max x16)
0c:00.0 MI210           16 GT/s x16 (max x16)
```

The board splits the CPU's 16 lanes x8/x8 when both top slots are used, and the RX 480 is in the second one. So 14 GB/s is about right for 4.0 x8. Moved the RX 480 to the bottom slot. That one runs off the chipset (x4 electrically, fine for a display card), and the MI210 is x16 all the way now. Moving it renumbered the buses: the MI210 went from 0c:00.0 to 0d:00.0 and from IOMMU group 28 to 29, so everything that hardcoded the address had to change. 0c:00.0 is now one of the card's own switch ports, so passing the old address would have handed the VM a bridge.

After the move: host→device 28.3 GB/s, device→host 28.6 GB/s (was 14.4 / 14.3). GEMM and device memory copy didn't change.

## Torch can't see the GPU on the host

`bench/run.sh baremetal` → `no GPU visible to torch`. The wheel is `2.15.0+rocm10.0`, so it's not a CPU build. `AMD_LOG_LEVEL=3` shows `hsa_init failed with 1000`. The `rocminfo` bundled with the wheel fails too (`HSA_STATUS_ERROR`), and `HSAKMT_DEBUG_LEVEL=7` gives `Failed to map remapped mmio page on gpu_mem 1`.

The system ROCm (10.1, `/opt/rocm/core-10.1`) works fine, so I loaded its HSA runtime instead of the bundled one:

```
LD_PRELOAD=/opt/rocm/core-10.1/lib/libhsa-runtime64.so.1 bench/run.sh baremetal
```

With 10.1 it prints `Skipping unsupported GPU: Polaris10 (node 2) ... unsupported doorbell type 1` and carries on with the MI210. So the RX 480 is probably what kills the 10.0 runtime; I didn't confirm by pulling the card.