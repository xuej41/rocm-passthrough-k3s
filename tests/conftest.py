"""A fake sysfs tree, laid out like the real one, built under tmp_path."""

from __future__ import annotations

from pathlib import Path

import pytest

MI210 = {"vendor": "0x1002", "device": "0x740f", "pci_class": "0x038000"}
RX480 = {"vendor": "0x1002", "device": "0x67df", "pci_class": "0x030000"}
BRIDGE = {"vendor": "0x1022", "device": "0x1483", "pci_class": "0x060400"}


class FakeSysfs:
    def __init__(self, root: Path):
        self.root = root
        self.devices = root / "bus" / "pci" / "devices"
        self.drivers = root / "bus" / "pci" / "drivers"
        self.groups = root / "kernel" / "iommu_groups"
        self.devices.mkdir(parents=True)
        self.drivers.mkdir(parents=True)
        self.groups.mkdir(parents=True)

    def add(
        self,
        address: str,
        *,
        vendor: str,
        device: str,
        pci_class: str,
        driver: str | None = "amdgpu",
        group: int | None = 1,
        link_speed: tuple[str, str] = ("16.0 GT/s PCIe", "16.0 GT/s PCIe"),
        link_width: tuple[str, str] = ("16", "16"),
        reset_method: str | None = "flr bus",
    ) -> Path:
        d = self.devices / address
        d.mkdir()
        (d / "vendor").write_text(vendor + "\n")
        (d / "device").write_text(device + "\n")
        (d / "class").write_text(pci_class + "\n")
        (d / "current_link_speed").write_text(link_speed[0] + "\n")
        (d / "max_link_speed").write_text(link_speed[1] + "\n")
        (d / "current_link_width").write_text(link_width[0] + "\n")
        (d / "max_link_width").write_text(link_width[1] + "\n")
        if reset_method is not None:
            (d / "reset_method").write_text(reset_method + "\n")
        if driver:
            drv = self.drivers / driver
            drv.mkdir(exist_ok=True)
            (d / "driver").symlink_to(drv)
        if group is not None:
            g = self.groups / str(group)
            (g / "devices").mkdir(parents=True, exist_ok=True)
            (d / "iommu_group").symlink_to(g)
            (g / "devices" / address).symlink_to(d)
        return d


@pytest.fixture
def sysfs(tmp_path: Path) -> FakeSysfs:
    return FakeSysfs(tmp_path / "sys")
