#!/usr/bin/env bash
# every iommu group and what's in it
set -euo pipefail
shopt -s nullglob

for g in $(find /sys/kernel/iommu_groups -mindepth 1 -maxdepth 1 -printf '%f\n' | sort -n); do
  echo "group $g"
  for d in /sys/kernel/iommu_groups/"$g"/devices/*; do
    echo "    $(lspci -nns "${d##*/}")"
  done
done
