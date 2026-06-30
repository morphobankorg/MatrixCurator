# src/benchmark/__main__.py
import os
import argparse
import asyncio
from src.benchmark.core.runner import discover_benchmarks, run_all


def main():
    parser = argparse.ArgumentParser(description="MatrixCurator Benchmark Runner")
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip dataset parsing and synchronization",
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Limit the number of dataset items to run"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent workers (default: 4)",
    )
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Additional target filters (currently unused)"
    )

    args = parser.parse_args()
    
    benchmark_dir = os.path.dirname(__file__)
    print(f"Discovering benchmarks in {benchmark_dir}")
    discover_benchmarks(benchmark_dir, filters=args.args)

    print(f"Running benchmarks (workers={args.workers}, limit={args.limit}, skip_sync={args.skip_sync})")
    asyncio.run(run_all(workers=args.workers, limit=args.limit, skip_sync=args.skip_sync))


if __name__ == "__main__":
    main()
