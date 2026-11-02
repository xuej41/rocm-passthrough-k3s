#!/usr/bin/env bash
# Create a q35 + UEFI Ubuntu 22.04 VM with the MI210 as a managed host device.
#
# Usage: MI210_ADDR=0000:0c:00.0 ISO=/path/ubuntu-22.04-live-server-amd64.iso vm/create-vm.sh
set -euo pipefail

: "${MI210_ADDR:?set MI210_ADDR, e.g. 0000:0c:00.0 (from lspci -D -d 1002:)}"
: "${ISO:?set ISO to the Ubuntu 22.04 server ISO}"
NAME="${NAME:-rocm-guest}"
RAM_MB="${RAM_MB:-32768}"
VCPUS="${VCPUS:-8}"
DISK_GB="${DISK_GB:-120}"   # ROCm + container images are big

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

echo "Created $NAME. If the guest logs 'BAR can't assign mem', merge vm/hostdev-snippet.xml with: virsh edit $NAME"
