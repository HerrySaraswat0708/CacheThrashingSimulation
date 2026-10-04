"""Four-core SE-mode baseline with a shared L2 acting as the LLC."""
import argparse
from pathlib import Path

import m5.stats
from m5.objects import GlobalInstTracker, LocalInstTracker
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

parser = argparse.ArgumentParser()
parser.add_argument("--binary", type=Path, required=True)
parser.add_argument("--llc", choices=("1MiB", "2MiB", "4MiB", "16MiB"), required=True)
parser.add_argument("--cores", type=int, choices=(1, 2, 4), default=4)
parser.add_argument("--window-insts", type=int, default=100_000)
parser.add_argument("workload_args", nargs=argparse.REMAINDER)
args = parser.parse_args()
if args.window_insts < 1:
    parser.error("--window-insts must be positive")
requires(isa_required=ISA.X86)

processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, isa=ISA.X86, num_cores=args.cores)
instruction_tracker = GlobalInstTracker(inst_thresholds=[args.window_insts])
for core in processor.get_cores():
    core.core.probeListener = LocalInstTracker(
        global_inst_tracker=instruction_tracker, start_listening=True
    )

board = SimpleBoard(
    clk_freq="2GHz",
    processor=processor,
    memory=SingleChannelDDR3_1600(size="1GiB"),
    cache_hierarchy=PrivateL1SharedL2CacheHierarchy(
        l1d_size="32KiB", l1i_size="32KiB", l2_size=args.llc,
        l1d_assoc=8, l1i_assoc=8, l2_assoc=16,
    ),
)
board.set_se_binary_workload(
    BinaryResource(local_path=str(args.binary.resolve())),
    arguments=args.workload_args,
)


def dump_window():
    index = 0
    while True:
        index += 1
        committed = instruction_tracker.getCounter()
        print(f"WINDOW_COMPLETE index={index} committed_instructions={committed}")
        m5.stats.dump()
        m5.stats.reset()
        instruction_tracker.resetCounter()
        instruction_tracker.addThreshold(args.window_insts)
        yield False


Simulator(board=board, on_exit_event={ExitEvent.MAX_INSTS: dump_window()}).run()
