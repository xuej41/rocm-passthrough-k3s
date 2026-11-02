#!/usr/bin/env bash
# List every IOMMU group and its devices. The MI210 should be alone
# (apart from PCI bridges) in its group.
set -euo pipefail
shopt -s nullglob

for g in $(find /sys/kernel/iommu_groups -mindepth 1 -maxdepth 1 -printf '%f\n' | sort -n); do
  echo "IOMMU group $g:"
  for d in /sys/kernel/iommu_groups/"$g"/devices/*; do
    echo "    $(lspci -nns "${d##*/}")"
  done
done
