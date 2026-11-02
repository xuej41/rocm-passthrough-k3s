# Host setup

1. **BIOS:** enable SVM and IOMMU. Keep **Above 4G decoding** on (the MI210 has a large BAR).
2. **Kernel command line:** add `iommu=pt` to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then run `sudo update-grub` and reboot.
3. **Packages:** `sudo apt install qemu-system-x86 libvirt-daemon-system libvirt-clients virtinst ovmf`, then `sudo usermod -aG libvirt,kvm $USER` and log in again.
4. Run `host/check-host.sh`, then `host/iommu-groups.sh`.
5. Run `passthrough-check` (from this repo). The MI210 should show its own group and `=> OK`.

**Verify:** the MI210 has its own IOMMU group and `virt-host-validate qemu` passes.

`vfio-pci.conf` is a fallback. Only use it if amdgpu won't release the card (see `docs/troubleshooting.md`).
