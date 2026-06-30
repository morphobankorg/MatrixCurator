"""Exceptions for benchmark control flow."""


class SkipBenchmark(Exception):
    """Indicates the run for this item is skipped."""

    pass


class FailBenchmark(Exception):
    """Indicates the run failed explicitly."""

    pass
