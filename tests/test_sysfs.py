import pytest
from conftest import BRIDGE, MI210, RX480

from passthrough_check.sysfs import (
    DeviceNotFoundError,
    find_gpus,
    inspect,
    normalize_address,
    parse_speed,
)

ADDR = "0000:03:00.0"


def levels(report):
    return [f.level for f in report.findings]


def test_isolated_mi210_is_ok(sysfs):
    sysfs.add(ADDR, **MI210, driver="vfio-pci", group=14)
    r = inspect(ADDR, sysfs.root, expect_driver="vfio-pci")
    assert r.device.driver == "vfio-pci"
    assert r.iommu_group == 14
    assert r.group_members == []
    assert r.reset_methods == ["flr", "bus"]
    assert r.findings == []
    assert r.ok


def test_short_address_accepted(sysfs):
    sysfs.add(ADDR, **MI210)
    assert inspect("03:00.0", sysfs.root).device.address == ADDR


@pytest.mark.parametrize("bad", ["", "3:0.0", "0000:03:00", "zz:00.0"])
def test_bad_address_rejected(bad):
    with pytest.raises(ValueError):
        normalize_address(bad)


def test_missing_device(sysfs):
    with pytest.raises(DeviceNotFoundError):
        inspect(ADDR, sysfs.root)


def test_wrong_driver_is_error(sysfs):
    sysfs.add(ADDR, **MI210, driver="amdgpu")
    r = inspect(ADDR, sysfs.root, expect_driver="vfio-pci")
    assert not r.ok
    assert "expected vfio-pci" in r.findings[0].message


def test_unbound_device_reports_none(sysfs):
    sysfs.add(ADDR, **MI210, driver=None)
    r = inspect(ADDR, sysfs.root, expect_driver="amdgpu")
    assert r.device.driver is None
    assert "driver is none" in r.findings[0].message


def test_no_iommu_group_is_error(sysfs):
    sysfs.add(ADDR, **MI210, group=None)
    r = inspect(ADDR, sysfs.root)
    assert r.iommu_group is None
    assert not r.ok


def test_shared_group_with_other_device_is_error(sysfs):
    sysfs.add(ADDR, **MI210, group=1)
    sysfs.add("0000:04:00.0", **RX480, group=1)
    r = inspect(ADDR, sysfs.root)
    assert [m.address for m in r.group_members] == ["0000:04:00.0"]
    assert not r.ok
    assert "shared with 0000:04:00.0" in r.findings[0].message


def test_bridges_and_sibling_functions_are_allowed(sysfs):
    sysfs.add(ADDR, **MI210, group=1)
    sysfs.add("0000:00:01.1", **BRIDGE, driver="pcieport", group=1)
    sysfs.add("0000:03:00.1", vendor="0x1002", device="0xaaf0", pci_class="0x040300", group=1)
    r = inspect(ADDR, sysfs.root)
    assert len(r.group_members) == 2
    assert r.ok, r.findings


def test_downtrained_link_is_warning_not_error(sysfs):
    sysfs.add(ADDR, **MI210, link_speed=("2.5 GT/s PCIe", "16.0 GT/s PCIe"), link_width=("8", "16"))
    r = inspect(ADDR, sysfs.root)
    assert levels(r) == ["warning", "warning"]
    assert r.ok


def test_unknown_link_speed_ignored(sysfs):
    sysfs.add(ADDR, **MI210, link_speed=("Unknown", "16.0 GT/s PCIe"))
    assert inspect(ADDR, sysfs.root).findings == []


def test_reset_method_empty_vs_missing(sysfs):
    sysfs.add(ADDR, **MI210, reset_method="")
    sysfs.add("0000:05:00.0", **MI210, group=2, reset_method=None)
    empty = inspect(ADDR, sysfs.root)
    missing = inspect("0000:05:00.0", sysfs.root)
    assert empty.reset_methods == []
    assert "no reset method" in empty.findings[0].message
    assert missing.reset_methods is None
    assert "not exposed" in missing.findings[0].message


def test_find_gpus_skips_bridges(sysfs):
    sysfs.add(ADDR, **MI210, group=1)
    sysfs.add("0000:04:00.0", **RX480, group=2)
    sysfs.add("0000:00:01.1", **BRIDGE, group=3)
    assert find_gpus(sysfs.root) == [ADDR, "0000:04:00.0"]


@pytest.mark.parametrize(
    "raw,expected",
    [("16.0 GT/s PCIe", 16.0), ("8.0 GT/s", 8.0), ("Unknown", None), (None, None)],
)
def test_parse_speed(raw, expected):
    assert parse_speed(raw) == expected
