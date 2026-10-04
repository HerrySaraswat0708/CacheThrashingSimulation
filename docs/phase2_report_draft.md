# Phase 2 report draft — cache thrashing prediction

**Submission target:** 31 October 2026  
**Status as of 2 October 2026:** implementation started; simulator results pending.

## 1. Research question

Can recent cache-state trajectories warn of a performance-degrading thrashing episode earlier than a single current measurement, and can a response reduce the resulting extra completion time?

## 2. Implemented experimental setup

The controlled C++ probe exercises sequential, strided, shuffled-random, and conflict-candidate accesses. The initial gem5 configuration specifies four x86 timing cores, private 32 KiB L1 caches, a shared 16-way last-level cache at 1, 2, or 4 MiB, a 16 MiB reference, and DDR3 memory. A global instruction tracker is configured to dump and reset statistics every 100,000 retired instructions. A reproducible run script records workload arguments, the binary hash, command, logs, and simulator statistics.

**Evidence currently available:** compilation and four native smoke runs completed. No gem5 build or simulation has completed in the current workspace. No event labels, risk estimates, warning metrics, or mitigation outcomes can yet be reported.

## 3. Experiments to report

| Experiment | Data to insert | Interpretation required |
| --- | --- | --- |
| Small hot set | Per-window LLC misses, MPKI, IPC, reference slowdown | Confirm cache-friendly negative control |
| One-pass stream | Same metrics plus reuse evidence | Separate compulsory/capacity misses from thrashing |
| Capacity reuse | Matched 1/2/4/16 MiB curves | Identify sustained re-fetches and slowdown |
| Set conflict | Actual mapped-set evidence or revised conflict construction | Confirm intended mechanism before labeling positive |
| Held-out controls | Event-rule precision/false alarms | Validate operational criterion |
| Seeded changing workloads | Event times, censoring, warning lead time | Compare current-state and trajectory models |
| Responses | Equal-work completion times and unnecessary-action costs | Compare no action, post-event, and early-warning policies |

## 4. Results and limitations

Insert figures, sample sizes, uncertainty across independent seeds, and precise metric definitions after the runs. Report any reduced sample size, failed cases, unsupported gem5 statistics, or unmet proposal targets. Keep native timing separate from simulated results.

## 5. Immediate next work

Build and validate gem5 in Linux; verify instruction-window collection and isolate the measurement region after setup; run and inspect the controlled pilot; then define and validate the thrashing event before generating stochastic labels.
