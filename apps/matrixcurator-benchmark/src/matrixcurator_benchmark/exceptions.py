class SkipBenchmark(Exception):
    """Exception raised when a benchmark should be skipped."""
    pass


class FailBenchmark(Exception):
    """Exception raised when a benchmark explicitly fails."""
    pass
