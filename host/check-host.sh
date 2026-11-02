#!/usr/bin/env bash
# Check that the host is ready for VFIO passthrough.
# Ready when the GPU has its own IOMMU group and virt-host-validate passes.
set -uo pipefail

ok()   { printf '  [ok]   %s\n' "$*"; }
bad()  { printf '  [FAIL] %s\n' "$*"; FAILED=1; }
FAILED=0

echo "== CPU virtualization (SVM)"
if grep -qw svm /proc/cpuinfo; then ok "svm flag present"; else bad "svm missing: enable SVM in BIOS"; fi

echo "== Kernel command line"
if grep -qw 'iommu=pt' /proc/cmdline; then ok "iommu=pt set"; else bad "iommu=pt missing from /proc/cmdline"; fi

echo "== IOMMU"
if [ -n "$(ls -A /sys/kernel/iommu_groups 2>/dev/null)" ]; then
  ok "$(find /sys/kernel/iommu_groups -mindepth 1 -maxdepth 1 | wc -l) IOMMU groups"
else
  bad "no IOMMU groups: enable IOMMU in BIOS"
fi
if sudo dmesg 2>/dev/null | grep -qiE 'AMD-Vi|IOMMU.*enabled'; then ok "AMD-Vi seen in dmesg"; fi

echo "== Packages"
for bin in qemu-system-x86_64 virsh virt-install virt-host-validate; do
  if command -v "$bin" >/dev/null; then ok "$bin"; else bad "$bin not installed"; fi
done
if ls /usr/share/OVMF/OVMF_CODE*.fd >/dev/null 2>&1; then ok "OVMF firmware"; else bad "OVMF not installed"; fi

echo "== GPUs"
lspci -nnk -d 1002: | grep -A3 -E 'VGA|Display|Processing' || true

echo "== Disk space (libvirt images)"
df -h /var/lib/libvirt/images 2>/dev/null || df -h /

echo "== virt-host-validate qemu"
if command -v virt-host-validate >/dev/null; then
  virt-host-validate qemu || FAILED=1
fi

echo
if [ "$FAILED" -eq 0 ]; then echo "Host looks ready. Now run: host/iommu-groups.sh"; else echo "Host NOT ready."; fi
exit "$FAILED"
