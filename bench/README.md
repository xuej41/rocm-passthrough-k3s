# bench

Same script on bare metal and in the guest: FP32/FP16 GEMM, pinned host↔device copies and device memory copy, median of 3

```bash
bench/run.sh baremetal    # on the host, before the VM takes the card
bench/run.sh guest        # in the guest
python3 bench/plot.py     # once both json files are in results/
```

- Needs ROCm PyTorch. Use the same torch version on both sides.

- On my host the HSA runtime bundled with the torch wheel won't start (see [LOG.md](../LOG.md)), so I run it with `LD_PRELOAD=/opt/rocm/core-10.1/lib/libhsa-runtime64.so.1`

- The MI210 slot is x8 while the RX 480 is in, so host↔device tops out around 14 GB/s
