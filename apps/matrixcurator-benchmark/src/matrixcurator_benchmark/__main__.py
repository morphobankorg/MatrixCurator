import argparse
import asyncio
import langfuse
import structlog

from matrixcurator_benchmark.setup import bootstrap_environment
from matrixcurator_benchmark.tools import run_tools_benchmarks
from matrixcurator_benchmark.retrieval import run_retrieval_benchmarks

logger = structlog.get_logger(__name__)

async def run_main():
    parser = argparse.ArgumentParser(description="MatrixCurator Benchmark Runner")
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip dataset parsing and synchronization",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Reset dataset cache and start fresh",
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
        "args", nargs="*", help="Target suites to run (e.g. tools, retrieval)"
    )

    args = parser.parse_args()
    
    targets = args.args if args.args else ["tools", "retrieval"]

    logger.info(
        "Starting benchmark execution...",
        workers=args.workers,
        limit=args.limit,
        skip_sync=args.skip_sync,
        no_cache=args.no_cache,
        targets=targets
    )
    
    docs_dict = await bootstrap_environment(
        limit=args.limit, skip_sync=args.skip_sync, no_cache=args.no_cache, targets=targets
    )

    if "tools" in targets:
        await run_tools_benchmarks(limit=args.limit, workers=args.workers, docs_dict=docs_dict)
        
    if "retrieval" in targets:
        await run_retrieval_benchmarks(limit=args.limit, workers=args.workers, docs_dict=docs_dict)

    lf = langfuse.Langfuse()
    lf.flush()
    logger.info("Benchmarks completed successfully.")


def main():
    asyncio.run(run_main())


if __name__ == "__main__":
    main()
