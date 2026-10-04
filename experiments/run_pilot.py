"""Run the reproducible controlled-workload pilot on a built x86 gem5."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

CASES = {
    # Case labels are hypotheses. gem5 measurements must confirm them.
    "small_hot": ("sequential", 32 * 1024, 64, 131072, 4, 7),
    "one_pass_stream": ("sequential", 8 * 1024 * 1024, 64, 131072, 4, 7),
    "capacity_reuse": ("sequential", 512 * 1024, 64, 131072, 4, 7),
    "set_conflict": ("conflict", 4 * 1024 * 1024, 64 * 1024, 131072, 4, 7),
}

parser = argparse.ArgumentParser()
parser.add_argument("--gem5", type=Path, required=True)
parser.add_argument("--binary", type=Path, required=True)
parser.add_argument("--output", type=Path, default=Path("results/pilot"))
parser.add_argument("--case", choices=tuple(CASES), action="append")
parser.add_argument("--llc", choices=("1MiB", "2MiB", "4MiB", "16MiB"), action="append")
parser.add_argument("--window-insts", type=int, default=100_000)
args = parser.parse_args()
if args.window_insts < 1:
    parser.error("--window-insts must be positive")

gem5 = args.gem5.resolve(strict=True)
binary = args.binary.resolve(strict=True)
output = args.output.resolve()
config = Path(__file__).with_name("gem5_config.py").resolve()
digest = hashlib.sha256(binary.read_bytes()).hexdigest()
gem5_digest = hashlib.sha256(gem5.read_bytes()).hexdigest()
config_digest = hashlib.sha256(config.read_bytes()).hexdigest()
revision = subprocess.run(
    ["git", "-C", str(gem5.parent), "rev-parse", "HEAD"],
    capture_output=True, text=True, check=False,
)
gem5_revision = revision.stdout.strip() if revision.returncode == 0 else None
for case in args.case or CASES:
    for llc in args.llc or ("1MiB", "2MiB", "4MiB", "16MiB"):
        outdir = output / case / llc
        if outdir.exists():
            raise SystemExit(f"Refusing to overwrite existing run: {outdir}")
        outdir.mkdir(parents=True)
        workload = [str(value) for value in CASES[case]]
        command = [str(gem5), f"--outdir={outdir}", str(config),
                   "--binary", str(binary), "--llc", llc,
                   "--window-insts", str(args.window_insts), *workload]
        metadata = {
            "case": case, "llc": llc, "workload_args": workload,
            "binary_sha256": digest, "command": command,
            "gem5_sha256": gem5_digest, "gem5_revision": gem5_revision,
            "config_sha256": config_digest, "window_insts": args.window_insts,
            "started_utc": datetime.now(timezone.utc).isoformat(),
        }
        (outdir / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
        with (outdir / "runner.log").open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    check=False)
        metadata["returncode"] = result.returncode
        metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (outdir / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"{case} {llc}: exit {result.returncode}; {outdir}", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
