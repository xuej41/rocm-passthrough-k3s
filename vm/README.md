# Passthrough VM

Order matters:

1. **Bare-metal benchmark first.** With the MI210 on `amdgpu` on the host, run `bench/run.sh baremetal`.
2. Create the VM: `MI210_ADDR=0000:0c:00.0 ISO=... vm/create-vm.sh`, then install Ubuntu 22.04.
3. Check on the host while the VM is running: `passthrough-check 0c:00.0 --expect-driver vfio-pci`
4. Install ROCm in the guest by following AMD's ROCm quick-start guide for Ubuntu 22.04 (`amdgpu-install`). Then run `rocm-smi`; it should list the MI210.
5. Run `bench/run.sh guest` in the guest, copy `bench/results/guest.json` back, and run `python3 bench/plot.py` (see `bench/README.md`).
6. `virsh shutdown rocm-guest`, then on the host run `passthrough-check 0c:00.0 --expect-driver amdgpu`. The card must return to amdgpu.

**Verify:** `rocm-smi` sees the MI210 in the guest.

Guest checks: `lspci -nnk | grep -A3 -i amd`, `dmesg | grep -i amdgpu`, `rocminfo | grep -i gfx` (MI210 = `gfx90a`).
