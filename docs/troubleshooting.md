# Troubleshooting

Log anything you hit here in `LOG.md` too.

## Guest logs "BAR can't assign mem"
The MI210's 64 GB BAR doesn't fit in the guest's default 64-bit PCI window.
1. Enlarge the window with `pcihole64` (see `vm/hostdev-snippet.xml`).
2. Turn ROM BAR off (`<rom bar='off'/>`).
3. Check the QEMU and OVMF versions (`qemu-system-x86_64 --version`, `dpkg -l ovmf`). Ubuntu 22.04's versions are too old for some GPUs, so try newer ones.

## amdgpu won't release the card
Symptom: the VM fails to start, `virsh start` hangs, or dmesg shows amdgpu errors during unbind.
- Bind `vfio-pci` to the MI210's device ID at boot, loaded before amdgpu: `host/vfio-pci.conf`.
- **Don't blacklist amdgpu.** The RX 480 needs it.
- Check with `passthrough-check 0c:00.0 --expect-driver vfio-pci`.

## The card doesn't come back to amdgpu after the VM stops
- Check `reset_method` with `passthrough-check`. An empty value means the device has no usable reset.
- Look in `dmesg` for reset or FLR errors and record them in LOG.md.

## The node shows `amd.com/gpu: 2`
The device plugin is counting the RX 480 too.

## Pod with `amd.com/gpu: 2` is Pending
Expected. The node only advertises 1 allocatable GPU, and `kubectl describe pod` shows `Insufficient amd.com/gpu`.

## Still stuck
Collect `passthrough-check --json`, `dmesg | grep -iE 'vfio|amdgpu|AMD-Vi'`, `virsh dumpxml <vm>` and the QEMU log (`/var/log/libvirt/qemu/<vm>.log`), and record what you ruled out in LOG.md.
