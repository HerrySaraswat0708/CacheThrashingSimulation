"""Export raw gem5 stats from successful pilot runs as a long-form CSV."""
import argparse
import csv
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, default=Path("results/pilot"))
parser.add_argument("--output", type=Path, default=Path("results/pilot_stats.csv"))
args = parser.parse_args()

rows = []
for run_path in sorted(args.input.glob("*/*/run.json")):
    run = json.loads(run_path.read_text())
    stats_path = run_path.with_name("stats.txt")
    if run.get("returncode") != 0 or not stats_path.exists():
        continue
    block = 0
    in_block = False
    for line in stats_path.read_text(errors="replace").splitlines():
        if "Begin Simulation Statistics" in line:
            block += 1
            in_block = True
            continue
        if "End Simulation Statistics" in line:
            in_block = False
            continue
        if not in_block or not line or line.startswith("#"):
            continue
        fields = line.split("#", 1)[0].split()
        if len(fields) < 2:
            continue
        name, value = fields[:2]
        try:
            float(value)
        except ValueError:
            continue
        rows.append((run["case"], run["llc"], block, name, value))

args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(("case", "llc", "block", "stat", "value"))
    writer.writerows(rows)
print(f"Exported {len(rows)} statistic rows to {args.output}")
