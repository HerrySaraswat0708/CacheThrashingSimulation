# Early prediction of cache thrashing

Clone this project with `git clone --recurse-submodules` to obtain the pinned
gem5 source revision. If the project was cloned without that option, run
`git submodule update --init --recursive` from the project root.

This workspace starts the implementation of [the Phase 1 proposal](Cache_Thrashing_Phase1_Proposal_edited.pdf). The proposed study compares cache behavior over time in changing multicore workloads, validates a measurable thrashing event, and then evaluates early warnings and responses. **No gem5 results or prediction results exist yet.** This README records what is implemented and what still needs evidence for the Phase 2 submission due **31 October 2026**.

## Current status (2 October 2026)

- `experiments/cache_probe.cpp`: deterministic sequential, strided, shuffled random, and conflict-candidate accesses. Each thread has its own 64-byte-aligned array. The printed checksum keeps reads observable to the compiler.
- `experiments/gem5_config.py`: x86 timing CPUs, four private 32 KiB L1 instruction/data caches, a shared 16-way L2 used as the last-level cache, and DDR3 memory. The shared-cache size is selectable: 1, 2, 4, or 16 MiB. The 16 MiB setting is the reference, subject to checking that it really accommodates the working set. A global retired-instruction tracker dumps and resets statistics every 100,000 completed instructions across the cores.
- `experiments/run_pilot.py`: four controlled cases crossed with the four cache sizes (16 planned runs). It saves the exact command, binary hash, simulator output, and exit status for every run and refuses to overwrite results.
- `experiments/export_stats.py`: exports raw numeric gem5 statistics to a long-form CSV, preserving each statistics-block number. The actual per-window counters still need simulator validation before analysis.
- The C++ probe compiled with MinGW g++ and all four access modes completed a small native smoke test. Those runs establish basic program operation only; their wall times are **not** gem5 measurements or thrashing evidence.

The checked-out `gem5/` source has no built simulator in this workspace. WSL access was denied here, so gem5 simulations could not be run locally. The instructions below are for a Linux environment with a working C++ compiler, Python, SCons, and gem5 build dependencies.

## Run the controlled pilot on Linux

From this directory:

```bash
cd gem5
scons build/X86/gem5.opt -j"$(nproc)"
cd ..
g++ -std=c++17 -O2 -static -pthread -Wall -Wextra \
  -o experiments/cache_probe experiments/cache_probe.cpp

# Validate one small simulation first.
python3 experiments/run_pilot.py \
  --gem5 gem5/build/X86/gem5.opt --binary experiments/cache_probe \
  --case small_hot --llc 1MiB --output results/smoke

# If the smoke run exits successfully and its stats.txt is credible:
python3 experiments/run_pilot.py \
  --gem5 gem5/build/X86/gem5.opt --binary experiments/cache_probe
python3 experiments/export_stats.py
```

Each run is stored under `results/pilot/<case>/<LLC>/`. Keep `run.json`, `runner.log`, `stats.txt`, and the gem5 configuration output together. The run script stops on the first failed run; use a new output directory when rerunning a case. Results are ignored by Git until reviewed, so they are not accidentally mistaken for validated findings.

The executable arguments are `PATTERN BYTES_PER_THREAD STRIDE_BYTES ACCESSES_PER_THREAD THREADS SEED`. For example:

```bash
./experiments/cache_probe strided 65536 256 2048 4 7
```

## Pilot design

| Case | Per-thread working set | Access sequence | Intended check |
| --- | ---: | --- | --- |
| `small_hot` | 32 KiB | Repeated sequential | Cache-friendly negative control |
| `one_pass_stream` | 8 MiB | One sequential pass | High miss count without reuse; negative control for *thrashing* |
| `capacity_reuse` | 512 KiB | 16 repeated passes | Shared-cache capacity pressure at smaller LLC sizes |
| `set_conflict` | 4 MiB | Repeated 64 KiB stride | Candidate set conflict; verify actual physical set mapping and misses in gem5 |

All cases use four threads and seed 7. Cache size changes while CPU, L1, memory, and workload inputs stay fixed. These labels express expected behavior, **not validated event labels**. In particular, allocator placement and physical address translation may alter whether the conflict candidate maps to one cache set. Each worker's initialization and thread setup are included in the current aggregate stats, so those stats cannot yet isolate a steady-state phase.

## Phase 2 work and evidence needed

1. **Simulator validation:** build gem5 on Linux; run the smoke case; verify four worker threads, cache hierarchy, program exit, and reported instruction and miss counters. Save gem5 revision and compiler version alongside results.
2. **Measurement windows:** validate that the configured 100,000 retired-instruction boundary and stat reset work as intended; add a clear start after allocation/initialization. Capture per-window LLC misses, MPKI, miss rate, evictions, instructions/cycle, and memory traffic. Confirm exact stat names in the built gem5 version and derive MPKI only from matching windows.
3. **Controlled positive/negative cases:** vary working-set size, stride, and thread count one at a time. Compare matched workloads at 1/2/4 MiB against the 16 MiB reference. Validate that the reference is sufficiently large. Treat one-pass streaming separately from repeatedly reusing evicted data.
4. **Operational thrashing rule:** choose a criterion based on observed reuse-related misses **and** completion-time or throughput loss against the reference; validate on held-out controlled parameters before using it to label stochastic runs. Record first-event time and right censoring when no event occurs.
5. **Changing workloads:** add the seeded phase-sequence generator from the proposal (working set, stride, locality, parallelism), run matched seeds across cache sizes, then compare current-state and trajectory-based warnings. The proposal's target is at least 30 seeds per 1/2/4 MiB size (90 main runs), subject to measured simulator runtime. Later compare response policies on equal completed work.

The first Phase 2 report should include the actual run count, hardware/software configuration, plots of windowed cache and throughput measurements, the controlled-case findings, any event-rule validation results, and a candid account of unfinished modeling. Do not report the proposal's two-window warning or 15% response improvement targets as findings until measured.

See [docs/phase2_report_draft.md](docs/phase2_report_draft.md) for a report outline that can be filled from saved runs.

The [experiment log](docs/experiment_log.md) records the 3 October 2026
preflight, including the exact pilot workload checks and the current gem5
execution blocker.
