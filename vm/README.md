# VM

Run `bench/run.sh baremetal` on the host first, while the card is still on amdgpu.

The ISO has to be somewhere libvirt can read (`/var/lib/libvirt/images`, not your home folder).

```bash
MI210_ADDR=0000:0c:00.0 ISO=/var/lib/libvirt/images/ubuntu-22.04.5-live-server-amd64.iso vm/create-vm.sh
passthrough-check 0c:00.0 --expect-driver vfio-pci    # on the host, with the VM running
```

Install Ubuntu through virt-manager, then install ROCm in the guest with `amdgpu-install` (AMD's quick start for 22.04). `rocm-smi` and `rocminfo | grep gfx90a` should both show the MI210. Then run `bench/run.sh guest`, copy `guest.json` back to the host, and run `python3 bench/plot.py`.

After `virsh shutdown rocm-guest` the card should go back to amdgpu:

```bash
passthrough-check 0c:00.0 --expect-driver amdgpu
```

If it doesn't, check `dmesg` for reset errors. The MI210 only has `bus` reset.

`hostdev-snippet.xml` is for when the guest can't fit the 64 GB BAR (`BAR can't assign mem` in the guest's dmesg).
