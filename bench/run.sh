#!/usr/bin/env bash
# Run the same benchmark on bare metal and in the guest.
# Usage: bench/run.sh baremetal|guest
#
# Writes bench/results/<label>.json (committed) and a raw log in
# bench/results/raw/ (gitignored). Once both JSON files exist, run
# `python3 bench/plot.py` to build the comparison table and charts.
set -euo pipefail

WHERE="${1:-}"
case "$WHERE" in
  baremetal|guest) ;;
  *) echo "usage: bench/run.sh baremetal|guest" >&2; exit 2 ;;
esac

HERE="$(cd "$(dirname "$0")" && pwd)"
RAW="$HERE/results/raw"
LOG="$RAW/${WHERE}-$(date +%Y%m%d-%H%M%S).txt"
mkdir -p "$RAW"

{
  echo "# $WHERE  $(date -Is)  $(uname -r)"
  rocm-smi --showproductname --showbus --showmeminfo vram || true
  echo "## rocm-bandwidth-test"
  if command -v rocm-bandwidth-test >/dev/null; then rocm-bandwidth-test; else echo "not installed"; fi
  echo "## gpu_bench.py"
  python3 "$HERE/gpu_bench.py" --label "$WHERE" --out "$HERE/results/$WHERE.json"
} 2>&1 | tee "$LOG"

echo
echo "Raw log: $LOG"
if [ -f "$HERE/results/baremetal.json" ] && [ -f "$HERE/results/guest.json" ]; then
  echo "Both runs present. Next: python3 bench/plot.py"
fi
