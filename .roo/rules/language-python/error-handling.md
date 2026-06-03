---
description: Exception handling, retries, and robust failure modes
globs: *.py
---
# Error Handling Standards

## 🎯 Directives
- ALWAYS use `Optional[T]` or `Union[T, ErrorType]` for expected failure modes (e.g., not finding an element) because return types can be statically checked, whereas exceptions cannot.
- ALWAYS use exceptions for truly exceptional, unexpected use cases (e.g., network failures, database down) that you wish to guard against.
- NEVER use exceptions for normal control flow or expected business logic failures.
- ALWAYS raise specific, documented exceptions (e.g., `ValueError`, `KeyError`, or custom domain exceptions) for failure states.
- ALWAYS use custom exceptions to express domain concepts (e.g., `OutOfStock`, `AllocationError`) rather than generic exceptions. These should be part of the ubiquitous language.
- NEVER return implicit `None` or magic numbers (like `-1`) to indicate an error. ALWAYS use explicit `Optional` or `Union` types so the typechecker can enforce handling.
- ALWAYS define a root exception (`class Error(Exception): pass`) for every module/package, and have all custom exceptions inherit from it.
- ALWAYS catch specific exceptions. NEVER use bare `except:` or `except Exception:` unless at the absolute top-level boundary for logging/crash reporting.
- ALWAYS use `contextlib.suppress(ExceptionType)` to explicitly ignore specific exceptions instead of `try: ... except: pass`.
- ALWAYS use the `tenacity` library (`@retry`, `Retrying`) to implement synchronous error recovery and exponential backoff for transient failures (e.g., network requests, database deadlocks).
- ALWAYS use `finally` blocks or context managers (`with`) to guarantee resource cleanup (e.g., closing files, releasing locks) regardless of success or failure.
- ALWAYS take advantage of each block in `try/except/else/finally`.
- ALWAYS consider `contextlib` and `with` statements for reusable `try/finally` behavior.
- ALWAYS use `else` blocks in `try/except` constructs to isolate the code that should only run if no exception occurred, keeping the `try` block as small as possible.

## 📝 Examples

### ✅ DO
```python
class MyModuleError(Exception):
    pass

class InvalidInputError(MyModuleError):
    pass

class OutOfStock(MyModuleError):
    pass

def process_data(data: str) -> dict:
    try:
        parsed = parse_json(data)
    except JSONDecodeError as e:
        raise InvalidInputError("Data is not valid JSON") from e
    else:
        return enrich_data(parsed)
```

### ❌ DON'T
```python
def process_data(data: str):
    try:
        parsed = parse_json(data)
        return enrich_data(parsed)
    except Exception:
        return None # Silent failure, returns None