#!/usr/bin/env bash
# q35 + UEFI Ubuntu 22.04 guest with the MI210 as a managed hostdev
# MI210_ADDR=0000:0c:00.0 ISO=/var/lib/libvirt/images/ubuntu-22.04.5-live-server-amd64.iso vm/create-vm.sh
set -euo pipefail

: "${MI210_ADDR:?set MI210_ADDR, e.g. 0000:0c:00.0}"
: "${ISO:?set ISO to the ubuntu 22.04 server iso}"
NAME="${NAME:-rocm-guest}"
RAM_MB="${RAM_MB:-16384}"   # host only has 32 GB
VCPUS="${VCPUS:-8}"
DISK_GB="${DISK_GB:-120}"   # rocm + container images are big

# virt-install wants pci_DDDD_BB_SS_F
HOSTDEV="pci_${MI210_ADDR//[:.]/_}"

virt-install \
  --name "$NAME" \
  --memory "$RAM_MB" \
  --vcpus "$VCPUS" \
  --cpu host-passthrough \
  --machine q35 \
  --boot uefi \
  --os-variant ubuntu22.04 \
  --disk size="$DISK_GB",bus=virtio \
  --network network=default,model=virtio \
  --cdrom "$ISO" \
  --graphics vnc \
  --hostdev "$HOSTDEV" \
  --noautoconsole
