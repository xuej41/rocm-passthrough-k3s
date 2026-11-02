from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from passthrough_check import __version__
from passthrough_check.sysfs import DeviceNotFoundError, Report, find_gpus, inspect

EXIT_OK, EXIT_PROBLEMS, EXIT_USAGE = 0, 1, 2


def _format(r: Report) -> str:
    d = r.device
    lines = [
        f"{d.address}  [{d.vendor}:{d.device}]  class {d.pci_class}",
        f"  driver        {d.driver or 'none'}",
        f"  iommu group   {r.iommu_group if r.iommu_group is not None else 'none'}",
    ]
    for m in r.group_members:
        tag = "bridge" if m.is_bridge else (m.driver or "none")
        lines.append(f"    member      {m.address} ({tag})")
    lines += [
        f"  link speed    {r.current_link_speed} (max {r.max_link_speed})",
        f"  link width    x{r.current_link_width} (max x{r.max_link_width})",
        "  reset method  "
        + ("unknown" if r.reset_methods is None else (" ".join(r.reset_methods) or "none")),
    ]
    for f in r.findings:
        lines.append(f"  {f.level.upper():7} {f.message}")
    lines.append("  => " + ("OK" if r.ok else "NOT READY"))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="passthrough-check",
        description="Report driver, IOMMU group, PCIe link and reset method for GPUs.",
    )
    p.add_argument("addresses", nargs="*", help="PCI addresses (default: auto-detect GPUs)")
    p.add_argument("--sysfs-root", type=Path, default=Path("/sys"), help=argparse.SUPPRESS)
    p.add_argument("--expect-driver", help="fail unless bound to this driver (e.g. vfio-pci)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    addrs = args.addresses or find_gpus(args.sysfs_root)
    if not addrs:
        print("no GPUs found", file=sys.stderr)
        return EXIT_USAGE

    reports = []
    for a in addrs:
        try:
            reports.append(inspect(a, args.sysfs_root, args.expect_driver))
        except (DeviceNotFoundError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return EXIT_USAGE

    if args.json:
        print(json.dumps([r.to_dict() for r in reports], indent=2))
    else:
        print("\n\n".join(_format(r) for r in reports))

    return EXIT_OK if all(r.ok for r in reports) else EXIT_PROBLEMS
