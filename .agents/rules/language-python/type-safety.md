---
description: Static typing, mypy configuration, and type hints
globs: *.py
---
# Type Safety Standards

## 🎯 Directives
- ALWAYS annotate function parameters and return types for all public APIs and cross-module interfaces.
- ALWAYS use `Optional[T]` (or `T | None` in Python 3.10+) when a value can be `None`. NEVER rely on implicit optionals.
- ALWAYS use `Union[A, B]` (or `A | B`) to define Sum Types, restricting state spaces and making illegal states unrepresentable.
- ALWAYS use `typing.Literal` to restrict variables to a specific set of raw values.
- ALWAYS use `typing.NewType` to enforce context-specific boundaries (e.g., `SanitizedString = NewType('SanitizedString', str)`).
- ALWAYS use `typing.Annotated` to attach context-specific metadata or constraints to types (e.g., `Annotated[int, ValueRange(3, 5)]`) to communicate intent, even if not statically checked.
- ALWAYS use `typing.Final` for constants and immutable class variables.
- ALWAYS use `typing.Protocol` for structural subtyping (duck typing). NEVER use `Union` of concrete classes for shared behavior.
- ALWAYS use `@typing.overload` when a function's return type depends dynamically on the input types.
- ALWAYS configure `mypy` strictly: enable `--strict-optional`, `--disallow-untyped-defs`, and `--disallow-any-generics`.
- NEVER use `Any` unless absolutely unavoidable. It neutralizes static analysis.
- NEVER use `typing.cast()` except as an absolute last resort to silence false positives from external stubs.
- NEVER use `TypedDict` for runtime validation; it is strictly for static analysis. Use `pydantic` for runtime checks.

## 📝 Examples

### ✅ DO
```python
from typing import Optional, Protocol

class EmailSender(Protocol):
    def send(self, address: str, body: str) -> bool: ...

def notify_user(user_id: int, sender: EmailSender) -> Optional[str]:
    if user_id < 0:
        return None
    sender.send("user@example.com", "Hello")
    return "Success"
```

### ❌ DON'T
```python
from typing import Any

# Missing return type, implicit None, uses Any, tightly coupled to concrete class
def notify_user(user_id, sender: Any):
    if user_id < 0:
        return None
    sender.send("user@example.com", "Hello")
    return "Success"