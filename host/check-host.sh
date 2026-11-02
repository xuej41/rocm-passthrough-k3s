#!/usr/bin/env bash
# sanity check before trying passthrough
set -uo pipefail

FAILED=0
ok()  { echo "ok    $*"; }
bad() { echo "FAIL  $*"; FAILED=1; }

if grep -qw svm /proc/cpuinfo; then ok "svm"; else bad "no svm flag, enable SVM in BIOS"; fi
if grep -qw 'iommu=pt' /proc/cmdline; then ok "iommu=pt"; else bad "iommu=pt not on the kernel cmdline"; fi

groups=$(find /sys/kernel/iommu_groups -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
if [ "$groups" -gt 0 ]; then ok "$groups iommu groups"; else bad "no iommu groups, enable IOMMU in BIOS"; fi

for bin in qemu-system-x86_64 virsh virt-install virt-host-validate; do
  if command -v "$bin" >/dev/null; then ok "$bin"; else bad "$bin missing"; fi
done
if ls /usr/share/OVMF/OVMF_CODE*.fd >/dev/null 2>&1; then ok "ovmf"; else bad "ovmf missing"; fi

echo
lspci -nnk -d 1002: | grep -A3 -E 'VGA|Display|Processing' || true
echo
df -h /var/lib/libvirt/images 2>/dev/null || df -h /
echo
if command -v virt-host-validate >/dev/null; then virt-host-validate qemu || FAILED=1; fi

exit "$FAILED"
