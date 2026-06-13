---
description: Profiling, memory management, and CPU/IO optimization
globs: *.py
---
# Performance and Optimization Standards

## 🎯 Directives
- NEVER optimize prematurely. ALWAYS profile first using `cProfile`, `memory_profiler`, or `Scalene` to identify actual bottlenecks.
- ALWAYS use `__slots__` for classes that will have millions of instances to prevent `__dict__` memory overhead.
- ALWAYS use `collections.deque` for FIFO queues to achieve O(1) appends and pops. NEVER use `list.pop(0)`.
- ALWAYS use `bisect` for O(log N) searches in sorted lists. NEVER use `list.index()`.
- ALWAYS use `heapq` for priority queues. NEVER use a `list` with continuous `.sort()` calls.
- ALWAYS use `memoryview` and `bytearray` for zero-copy I/O operations. NEVER slice large `bytes` objects.
- ALWAYS use `numpy` arrays and `numexpr` for heavy vectorized math. Avoid creating large temporary arrays in memory.
- ALWAYS use `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` for CPU-bound tasks to bypass the GIL.
- ALWAYS use `asyncio` or `concurrent.futures.ThreadPoolExecutor` for I/O-bound tasks.
- ALWAYS use `subprocess` to manage child processes for parallel execution.
- ALWAYS use threads for blocking I/O, but avoid them for parallelism due to the GIL.
- ALWAYS use `Lock` to prevent data races in threads.
- ALWAYS use `Queue` to coordinate work between threads.
- ALWAYS achieve highly concurrent I/O with coroutines (`asyncio`).
- ALWAYS consider `concurrent.futures` for true parallelism.
- ALWAYS use `tracemalloc` to understand memory usage and leaks.
- ALWAYS use Numba (`@njit`) or Cython to compile tight, CPU-bound mathematical loops to machine code.
- ALWAYS use probabilistic data structures (e.g., HyperLogLog, Bloom Filters) when exact counts/membership are not required but memory is strictly constrained.
- ALWAYS use generators (`yield`) to stream large datasets instead of loading everything into RAM.
- NEVER optimize prematurely. ALWAYS profile first using `cProfile`, `line_profiler`, `memory_profiler`, `Scalene`, or `py-spy` to identify actual bottlenecks.
- ALWAYS encapsulate performance-critical code inside functions rather than running it at the module level to benefit from faster local variable lookups (`LOAD_FAST` vs `LOAD_GLOBAL`).
- ALWAYS initialize all instance attributes inside `__init__` to leverage the PEP 412 Key-Sharing Dictionary optimization. NEVER create new instance attributes after `__init__`.
- ALWAYS use `functools.lru_cache(maxsize=2**N)` with a power of 2 for optimal performance, or `functools.cache` if memory is not a concern.
- ALWAYS use `all()` and `any()` for short-circuiting boolean evaluations on iterables instead of `functools.reduce()`.
- ALWAYS use `run_in_executor` to offload CPU-bound or blocking I/O functions to a separate thread or process when using `asyncio`, to avoid blocking the event loop.
- ALWAYS use `set` or `frozenset` for membership testing (`in` operator) on large collections. NEVER use `list` or `tuple` for O(N) lookups.
- ALWAYS use `set` operations (e.g., `set(a) - set(b)`) instead of iterating over lists to find differences or invalid fields.
- ALWAYS use `collections.defaultdict` and `collections.Counter` instead of manual dictionary manipulation for grouping and counting.
- ALWAYS use `"".join()` to concatenate strings in a loop. NEVER use the `+=` operator for string concatenation in loops due to quadratic memory reallocation costs.
- ALWAYS consider tuning the garbage collector (`gc.set_threshold()`) or temporarily disabling it (`gc.disable()`) during massive object creation phases to prevent GC pauses.
- ALWAYS use `Polars`, `Dask`, or `Ray` for data processing tasks that exceed single-machine memory limits or require distributed cluster computing.
- ALWAYS avoid defining functions within functions (unless creating a closure) to prevent needless `MAKE_FUNCTION` bytecode overhead on every call.
- ALWAYS consider using the `dis` module to disassemble and understand Python bytecode for micro-optimizations.
- NEVER run performance-critical loops at the global module scope; ALWAYS wrap them in a function to avoid `LOAD_GLOBAL` overhead.

## 📝 Examples

### ✅ DO
```python
import collections

queue = collections.deque()
queue.append(item)
processed = queue.popleft() # O(1)
```

### ❌ DON'T
```python
queue = []
queue.append(item)
processed = queue.pop(0) # O(N)
```

### ✅ DO
```python
import functools

@functools.lru_cache(maxsize=128)
def expensive_computation(x: int) -> int:
    return x * x

def process_items(items: list[str]) -> str:
    # Fast local variable lookup and efficient string concatenation
    valid_items = {"apple", "banana", "orange"} # O(1) lookup
    return "".join(item for item in items if item in valid_items)
```

### ❌ DON'T
```python
# Global scope loop is slow due to LOAD_GLOBAL
result = ""
valid_items = ["apple", "banana", "orange"] # O(N) lookup

for item in items:
    if item in valid_items:
        result += item # Quadratic memory reallocation