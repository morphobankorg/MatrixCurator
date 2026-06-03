---
description: Naming conventions for variables, classes, functions, and files
globs: *.py
---
# Naming Conventions Standards

## 🎯 Directives
- ALWAYS use `lowercase_underscore` (snake_case) for functions, variables, methods, and module names.
- ALWAYS use `CapitalizedWord` (PascalCase) for classes and exception names.
- ALWAYS use `ALL_CAPS_WITH_UNDERSCORES` for module-level constants.
- ALWAYS use a single leading underscore (`_protected`) for protected instance attributes and internal module functions.
- ALWAYS use a double leading underscore (`__private`) ONLY for private instance attributes to invoke name mangling and prevent subclass collisions.
- ALWAYS name the first parameter of instance methods `self`.
- ALWAYS name the first parameter of class methods `cls`.
- ALWAYS name Commands using the imperative mood (verb phrases, e.g., `Allocate`, `CreateBatch`).
- ALWAYS name Events using past-tense verb phrases (e.g., `Allocated`, `BatchCreated`).
- ALWAYS suffix exception classes with `Error` (e.g., `OutOfStockError`).
- ALWAYS suffix mixin classes with `Mixin` (e.g., `JSONSerializableMixin`).
- ALWAYS use language-agnostic, kebab-case, lowercase filenames for markdown/documentation files (e.g., `naming-conventions.md`).

## 📝 Examples

### ✅ DO
```python
MAX_RETRIES = 3

class OrderProcessor:
    def __init__(self):
        self._internal_cache = {}
        
    def process_order(self, order_id: str) -> None:
        pass

@dataclass
class OrderCreated(Event):
    order_id: str
```

### ❌ DON'T
```python
MaxRetries = 3

class order_processor:
    def ProcessOrder(self, OrderId: str):
        pass

@dataclass
class CreateOrderEvent(Event): # Imperative mood for an event
    order_id: str