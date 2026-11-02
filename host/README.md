# Host setup

- BIOS: SVM and IOMMU on, Above 4G decoding on (the MI210 has a 64 GB BAR)
- add `iommu=pt` to `GRUB_CMDLINE_LINUX_DEFAULT`, `sudo update-grub`, reboot
- `sudo apt install qemu-system-x86 libvirt-daemon-system libvirt-clients virtinst ovmf virt-manager`, then `sudo usermod -aG libvirt,kvm $USER` and log back in

Then `host/check-host.sh` and `host/iommu-groups.sh`. On this board the MI210 gets IOMMU group 28 to itself.

`vfio-pci.conf` binds vfio-pci to the MI210 at boot. I don't normally use it, since libvirt's managed hostdev does the unbind when the VM starts. It's there in case amdgpu won't let go of the card.
