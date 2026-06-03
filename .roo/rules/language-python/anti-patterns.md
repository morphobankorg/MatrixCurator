---
description: Python anti-patterns and practices to avoid
globs: *.py
---
# Anti-Patterns Standards

## 🎯 Directives
- NEVER violate the Law of Least Surprise; if a function's behavior or implementation is surprising, it MUST be refactored or heavily documented.
- NEVER use mutable objects (`list`, `dict`, `set`) as default arguments in function signatures.
- NEVER use `time.sleep()` to wait for UI or asynchronous state changes; ALWAYS use explicit polling/wait loops.
- NEVER use `monkeypatching` or `mock.patch` for internal application dependencies; ALWAYS use Dependency Injection and Fakes.
- NEVER use `Any` in type hints unless absolutely necessary; it defeats static analysis.
- NEVER use `IntEnum` or `IntFlag`; they allow implicit integer conversion and break type safety.
- NEVER use `dict` or `tuple` for heterogeneous domain concepts; ALWAYS use `@dataclass` or standard classes.
- NEVER use `list` to store millions of numeric primitives; ALWAYS use `array.array` or `numpy.array`.
- NEVER use `map()` or `filter()` with lambdas; ALWAYS use list comprehensions or generator expressions.
- NEVER use `is` to compare values (like strings or integers); ALWAYS use `==`. `is` is strictly for identity (e.g., `is None`).
- NEVER implement `__del__` for resource cleanup; ALWAYS use context managers (`with`).
- NEVER raise `NotImplementedError` in a subclass to disable inherited behavior; this violates the Liskov Substitution Principle.
- NEVER use the ORM for complex read queries that cause SELECT N+1 issues; ALWAYS use raw SQL or denormalized views for read models.
- NEVER use the `time` module for timezone math; ALWAYS use `datetime` and `pytz` (or `zoneinfo`).
- NEVER use timezone-unaware `datetime` objects (e.g., `datetime.utcnow()`, `datetime.now()`). ALWAYS use timezone-aware objects (e.g., `datetime.now(tz=...)`).
- NEVER use `pickle` for untrusted data; ALWAYS use JSON or another safe serialization format.
- NEVER use `float` for exact math (e.g., currency); ALWAYS use `decimal.Decimal`.
- NEVER use `list.pop(0)` for queues; ALWAYS use `collections.deque`.
- NEVER use `list.index()` on sorted lists; ALWAYS use `bisect`.
- NEVER use `list` with `.sort()` for priority queues; ALWAYS use `heapq`.
- NEVER slice `bytes` for large I/O; ALWAYS use `memoryview` or `bytearray` for zero-copy operations.
- NEVER use `eval()` on untrusted strings; ALWAYS use `ast.literal_eval()`.
- NEVER use wildcard imports (`from module import *`).
- NEVER use blocking I/O (e.g., `requests`, `time.sleep()`) inside `async def` coroutines.
- NEVER use `ThreadPoolExecutor` for CPU-bound tasks; ALWAYS use `ProcessPoolExecutor` or `multiprocessing`.
- NEVER use `ProcessPoolExecutor` for I/O-bound tasks; ALWAYS use `ThreadPoolExecutor` or `asyncio`.
- NEVER use `__dict__` for classes with millions of instances; ALWAYS use `__slots__`.
- NEVER write long `isinstance` chains; ALWAYS use `@functools.singledispatch`.
- NEVER call `super(Class, self)` in Python 3; ALWAYS use the zero-argument `super()`.
- NEVER define `__init__` or state in Mixin classes.
- NEVER implement `__getattr__` without also implementing `__setattr__` to prevent state desynchronization.
- NEVER use `__new__` in metaclasses for simple subclass validation or registration; ALWAYS use `__init_subclass__`.
- NEVER use metaclasses for composable class extensions; ALWAYS prefer class decorators.
- NEVER unpack more than three variables when functions return multiple values; ALWAYS use a small class or `namedtuple`.
- NEVER use more than two control subexpressions in comprehensions; they become unreadable.
- NEVER inject data into generators with `send` or cause state transitions with `throw`; they add unnecessary complexity.
- NEVER use setter and getter methods; ALWAYS use plain attributes or `@property`.
- NEVER create new thread instances for on-demand fan-out; ALWAYS use `ThreadPoolExecutor`.
- NEVER block the `asyncio` event loop; ALWAYS use `run_in_executor` for blocking I/O.
- NEVER read `__annotations__` directly; ALWAYS use `inspect.get_annotations()`.
- NEVER use `TypedDict` for runtime validation; ALWAYS use `pydantic`.
- NEVER use `Union` of concrete classes for shared behavior; ALWAYS use `typing.Protocol`.
- NEVER use `issubclass()` on a Protocol that contains data attributes.
- NEVER use `assert` for runtime data validation; ALWAYS raise `ValueError` or custom exceptions.
- NEVER use `assertContains` with raw HTML strings in tests; ALWAYS parse HTML with `lxml` or similar.
- NEVER use raw `assert` in `unittest.TestCase`; ALWAYS use `self.assertEqual`, `self.assertTrue`, etc.
- NEVER mock internal framework utilities (e.g., Django messages); assert against the resulting state.
- NEVER patch a dependency where it is defined; ALWAYS patch it in the target namespace where it is used.
- NEVER use `mock.patch` without `spec=True` or passing the target class to `spec`.
- NEVER couple Domain Models to ORM classes (e.g., inheriting from `db.Model` or `Base`). ALWAYS use classical mapping or separate ORM models.
- NEVER pass Domain Objects into Service Layer functions from the outside (e.g., from API endpoints); ALWAYS pass primitives to fully decouple the Service Layer from the Domain Model.
- NEVER subclass built-in types like `dict`, `list`, or `str` directly; ALWAYS use `collections.UserDict`, `collections.UserList`, or `collections.UserString` to avoid C-level method bypass bugs.
- NEVER create instance attributes outside of `__init__`; it defeats the PEP 412 Key-Sharing Dictionary memory optimization.
- NEVER depend on string or integer interning for equality checks. ALWAYS use `==` instead of `is` to compare strings or integers.
- NEVER use `functools.reduce()` for boolean checks; ALWAYS use `all()` or `any()` to benefit from short-circuiting.
- NEVER organize code by types (e.g., `exceptions.py`, `functions.py`); ALWAYS organize by features.
- NEVER perform a `SELECT` to check for existence before an `INSERT` to enforce uniqueness; ALWAYS rely on database `UNIQUE` constraints and catch the exception to avoid race conditions.

## 📝 Examples

### ❌ DON'T
```python
def add_item(item, items=[]):
    items.append(item)
    return items
```

### ✅ DO
```python
def add_item(item, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items