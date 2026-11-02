"""Reads the passthrough-relevant bits of sysfs.

Everything takes a sysfs_root so the tests can point it at a fake tree.

    bus/pci/devices/<addr>/
        vendor, device, class
        driver          -> symlink to the bound driver
        iommu_group     -> symlink to kernel/iommu_groups/<n>
        {current,max}_link_{speed,width}
        reset_method    (kernel 5.15+)
    kernel/iommu_groups/<n>/devices/*
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

AMD_VENDOR = "0x1002"
NVIDIA_VENDOR = "0x10de"
GPU_VENDORS = (AMD_VENDOR, NVIDIA_VENDOR)

# class 0x03 = display, 0x12 = processing accelerator
GPU_CLASS_PREFIXES = ("0x03", "0x12")
# 0x0604 = pci bridge, fine to have in the group
BRIDGE_CLASS_PREFIX = "0x0604"

_ADDR_FULL = re.compile(r"^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$")
_ADDR_SHORT = re.compile(r"^[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$")
_SPEED = re.compile(r"([\d.]+)\s*GT/s")


class DeviceNotFoundError(LookupError):
    pass


@dataclass
class PciDevice:
    address: str
    vendor: str | None
    device: str | None
    pci_class: str | None
    driver: str | None

    @property
    def is_bridge(self) -> bool:
        return bool(self.pci_class and self.pci_class.startswith(BRIDGE_CLASS_PREFIX))

    @property
    def slot(self) -> str:
        """address without the function, e.g. 0000:03:00"""
        return self.address.rsplit(".", 1)[0]


@dataclass
class Finding:
    level: str  # "error" or "warning"
    message: str


@dataclass
class Report:
    device: PciDevice
    iommu_group: int | None
    group_members: list[PciDevice]
    current_link_speed: str | None
    max_link_speed: str | None
    current_link_width: str | None
    max_link_width: str | None
    reset_methods: list[str] | None  # None if the kernel doesn't have reset_method
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.level == "error" for f in self.findings)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ok"] = self.ok
        return d


def normalize_address(addr: str) -> str:
    """03:00.0 or 0000:03:00.0 -> 0000:03:00.0"""
    a = addr.strip().lower()
    if _ADDR_SHORT.match(a):
        a = "0000:" + a
    if not _ADDR_FULL.match(a):
        raise ValueError(f"not a PCI address: {addr!r} (expected e.g. 0000:03:00.0)")
    return a


def _read(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return None


def _link_name(path: Path) -> str | None:
    """name of what a symlink points to"""
    if not path.is_symlink():
        return None
    return Path(path.readlink()).name


def _devices_dir(sysfs_root: Path) -> Path:
    return sysfs_root / "bus" / "pci" / "devices"


def read_device(address: str, sysfs_root: Path = Path("/sys")) -> PciDevice:
    address = normalize_address(address)
    d = _devices_dir(sysfs_root) / address
    if not d.exists():
        raise DeviceNotFoundError(f"no PCI device {address} under {d.parent}")
    return PciDevice(
        address=address,
        vendor=_read(d / "vendor"),
        device=_read(d / "device"),
        pci_class=_read(d / "class"),
        driver=_link_name(d / "driver"),
    )


def find_gpus(sysfs_root: Path = Path("/sys"), vendors=GPU_VENDORS) -> list[str]:
    """addresses of AMD/NVIDIA display and accelerator devices"""
    root = _devices_dir(sysfs_root)
    if not root.is_dir():
        return []
    found = []
    for entry in sorted(root.iterdir()):
        vendor = _read(entry / "vendor")
        cls = _read(entry / "class") or ""
        if vendor in vendors and cls.startswith(GPU_CLASS_PREFIXES):
            found.append(entry.name)
    return found


def parse_speed(value: str | None) -> float | None:
    """'16.0 GT/s PCIe' -> 16.0, None for Unknown"""
    if not value:
        return None
    m = _SPEED.search(value)
    return float(m.group(1)) if m else None


def _parse_width(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def inspect(
    address: str,
    sysfs_root: Path = Path("/sys"),
    expect_driver: str | None = None,
) -> Report:
    dev = read_device(address, sysfs_root)
    d = _devices_dir(sysfs_root) / dev.address

    group_name = _link_name(d / "iommu_group")
    group = int(group_name) if group_name and group_name.isdigit() else None

    members: list[PciDevice] = []
    if group is not None:
        gdir = sysfs_root / "kernel" / "iommu_groups" / str(group) / "devices"
        if gdir.is_dir():
            for m in sorted(gdir.iterdir()):
                if m.name == dev.address:
                    continue
                try:
                    members.append(read_device(m.name, sysfs_root))
                except (DeviceNotFoundError, ValueError):
                    members.append(PciDevice(m.name, None, None, None, None))

    raw_reset = _read(d / "reset_method")
    reset_methods = raw_reset.split() if raw_reset is not None else None

    report = Report(
        device=dev,
        iommu_group=group,
        group_members=members,
        current_link_speed=_read(d / "current_link_speed"),
        max_link_speed=_read(d / "max_link_speed"),
        current_link_width=_read(d / "current_link_width"),
        max_link_width=_read(d / "max_link_width"),
        reset_methods=reset_methods,
    )
    report.findings = evaluate(report, expect_driver)
    return report


def evaluate(r: Report, expect_driver: str | None = None) -> list[Finding]:
    out: list[Finding] = []

    if expect_driver is not None and r.device.driver != expect_driver:
        out.append(
            Finding("error", f"driver is {r.device.driver or 'none'}, expected {expect_driver}")
        )

    if r.iommu_group is None:
        out.append(
            Finding(
                "error",
                "no IOMMU group: enable SVM/IOMMU in BIOS and check the kernel command line",
            )
        )
    else:
        for m in r.group_members:
            if m.is_bridge or m.slot == r.device.slot:
                continue  # bridges and other functions of the same card are fine
            out.append(
                Finding(
                    "error",
                    f"IOMMU group {r.iommu_group} is shared with {m.address} "
                    f"(class {m.pci_class}, driver {m.driver or 'none'})",
                )
            )

    cur, mx = parse_speed(r.current_link_speed), parse_speed(r.max_link_speed)
    if cur is not None and mx is not None and cur < mx:
        out.append(
            Finding(
                "warning",
                f"link speed {r.current_link_speed} below max {r.max_link_speed} "
                "(normal at idle; check under load)",
            )
        )
    cw, mw = _parse_width(r.current_link_width), _parse_width(r.max_link_width)
    if cw is not None and mw is not None and cw < mw:
        out.append(Finding("warning", f"link width x{cw} below max x{mw}: check slot/riser"))

    if r.reset_methods is None:
        out.append(Finding("warning", "reset_method not exposed (kernel < 5.15?)"))
    elif not r.reset_methods:
        out.append(Finding("warning", "no reset method: card may not recover after the VM stops"))

    return out
