import json

from conftest import MI210, RX480

from passthrough_check.cli import EXIT_OK, EXIT_PROBLEMS, EXIT_USAGE, main

ADDR = "0000:03:00.0"


def run(sysfs, *args):
    return main(["--sysfs-root", str(sysfs.root), *args])


def test_text_output_ok(sysfs, capsys):
    sysfs.add(ADDR, **MI210, driver="vfio-pci", group=14)
    assert run(sysfs, ADDR) == EXIT_OK
    out = capsys.readouterr().out
    assert "driver        vfio-pci" in out
    assert "iommu group   14" in out
    assert "=> OK" in out


def test_json_output(sysfs, capsys):
    sysfs.add(ADDR, **MI210, group=14)
    assert run(sysfs, "--json", ADDR) == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data[0]["device"]["address"] == ADDR
    assert data[0]["iommu_group"] == 14
    assert data[0]["ok"] is True


def test_autodetect_all_gpus(sysfs, capsys):
    sysfs.add(ADDR, **MI210, group=1)
    sysfs.add("0000:04:00.0", **RX480, group=2)
    assert run(sysfs, "--json") == EXIT_OK
    assert len(json.loads(capsys.readouterr().out)) == 2


def test_expect_driver_mismatch_exits_1(sysfs, capsys):
    sysfs.add(ADDR, **MI210, driver="amdgpu")
    assert run(sysfs, "--expect-driver", "vfio-pci", ADDR) == EXIT_PROBLEMS
    assert "NOT READY" in capsys.readouterr().out


def test_missing_device_exits_2(sysfs, capsys):
    assert run(sysfs, ADDR) == EXIT_USAGE
    assert "no PCI device" in capsys.readouterr().err


def test_no_gpus_exits_2(sysfs, capsys):
    assert run(sysfs) == EXIT_USAGE
