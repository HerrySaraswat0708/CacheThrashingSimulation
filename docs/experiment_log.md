# Experiment log

## 2026-10-03: requested simulation start

- Attempted to begin the README's controlled gem5 pilot. The required
  `gem5/build/X86/gem5.opt` executable is absent, so the smoke run could not
  be launched and no simulator result directory was created.
- Rechecked `wsl --status` and `wsl --list --quiet`; both returned
  `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`. Docker and Podman commands
  were unavailable. The local MinGW toolchain is present, but it does not
  provide the Linux gem5 build environment required by this project.
- Status: zero gem5 runs started. The next executable step is the Linux build
  and `small_hot` smoke command in `README.md`, followed by inspection of its
  exit status and statistics before the 16-run pilot.

## 2026-10-03: gem5 pilot preflight

- Project: controlled cache-thrashing pilot described in `README.md`.
- gem5 source revision: `f5c5a6e390f55dd5984977815bf9d0bd05da6945`.
- Simulator: `gem5/build/X86/gem5.opt` is absent; no gem5 simulation was run.
- Linux access: `wsl --status` and `wsl --list --quiet` returned
  `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`. No Docker or Podman command
  was available in this session.
- Python syntax check passed for `run_pilot.py`, `gem5_config.py`, and
  `export_stats.py`.
- The checked-out gem5 global instruction tracker example uses the same
  `LocalInstTracker` attachment, counter reset, and threshold rearming pattern
  as `experiments/gem5_config.py`. Runtime behavior still needs validation.

The C++ probe was rebuilt on Windows with `g++ -std=c++17 -O2 -pthread
-Wall -Wextra`. All four **exact pilot workloads** completed natively:

| Case | Pattern | Bytes per thread | Stride bytes | Accesses per thread | Threads | Seed | Checksum |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `small_hot` | sequential | 32768 | 64 | 131072 | 4 | 7 | 1072955392 |
| `one_pass_stream` | sequential | 8388608 | 64 | 131072 | 4 | 7 | 274877120512 |
| `capacity_reuse` | sequential | 524288 | 64 | 131072 | 4 | 7 | 17179082752 |
| `set_conflict` | conflict | 4194304 | 65536 | 131072 | 4 | 7 | 135292780544 |

These checksums establish workload completion only. Native timings and these
runs do not establish cache misses, thrashing, or any gem5 result.

Next, from a Linux environment with gem5 build dependencies available, run
the build and smoke commands in `README.md`. Inspect the smoke run's
`runner.log`, `stats.txt`, configuration, and exit status before starting the
full 16-run pilot.
