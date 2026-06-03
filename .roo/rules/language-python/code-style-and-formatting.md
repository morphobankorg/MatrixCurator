---
description: Python code style, PEP 8, and idiomatic formatting
globs: *.py
---
# Code Style and Formatting Standards

## 🎯 Directives
- ALWAYS choose the collection type that explicitly communicates your intent: `list` for mutable sequences, `tuple` for fixed-size immutable records, `set` for uniqueness, and `dict` for key-value mapping.
- ALWAYS use specialized collections (`collections.Counter`, `collections.defaultdict`, `frozenset`) when they match the domain problem to reduce boilerplate and communicate intent.
- ALWAYS use `for` loops for side effects, `while` loops for condition-based iteration, and comprehensions for transforming collections without side effects.
- NEVER use static indexing (e.g., `my_list[4]`) on dynamic collections like lists or dicts; ALWAYS use dynamic indexing or iteration. Static indexing is only acceptable for tuples or fixed-format parsing.
- ALWAYS adhere strictly to PEP 8 formatting guidelines.
- ALWAYS prefer Pythonic code and module-level functions instead of Java-like class spaghetti (e.g., avoid creating classes with only static methods or a single `__init__` and `run` method).
- ALWAYS use 4 spaces for indentation. NEVER use tabs.
- ALWAYS limit line length to 79 characters.
- ALWAYS use interpolated f-strings (`f"{var}"`) for string formatting. NEVER use `%s` or `.format()`.
- ALWAYS prefer multiple assignment unpacking over explicit numeric indexing (e.g., `a, b = b, a`).
- ALWAYS use `enumerate()` when iterating over a sequence and needing the index.
- ALWAYS use `zip()` to iterate over multiple sequences in parallel.
- ALWAYS use the walrus operator (`:=`) to assign and evaluate expressions simultaneously, avoiding redundant computation.
- ALWAYS prefer list, dict, and set comprehensions over `map()` and `filter()`.
- ALWAYS use generator expressions `(...)` instead of list comprehensions `[...]` for large datasets to prevent memory exhaustion.
- ALWAYS use `yield from` to compose multiple nested generators.
- ALWAYS use `match/case` (Python 3.10+) for structural parsing and destructuring.
- ALWAYS enforce clarity with keyword-only and positional-only arguments.
- ALWAYS define function decorators with `functools.wraps` to preserve metadata.
- ALWAYS use `functools.partial` instead of `lambda` functions for better readability, reusability, and to overcome lambda's single-line limitation.
- ALWAYS use `@contextlib.contextmanager` to create simple context managers instead of writing full classes with `__enter__` and `__exit__`.
- ALWAYS use `None` and docstrings to specify dynamic default arguments.
- ALWAYS consider `itertools` for working with iterators and generators.
- ALWAYS prefer public attributes over private ones unless you strictly need to avoid naming conflicts with subclasses.
- ALWAYS use `try/except/else/finally` blocks appropriately: `else` for success paths, `finally` for guaranteed cleanup.
- ALWAYS use `for/else` and `while/else` constructs to handle loop exhaustion without using boolean flags.
- ALWAYS group imports in three alphabetical sections: standard library, third-party, and local modules.
- ALWAYS design sequence constructors to take data as an iterable argument, matching the behavior of built-in sequence types.

## 📝 Examples

### ✅ DO
```python
for rank, (name, calories) in enumerate(snacks, 1):
    print(f'#{rank}: {name} has {calories} calories')

if (count := fresh_fruit.get('banana', 0)) >= 2:
    make_smoothies(count)
```

### ❌ DON'T
```python
for i in range(len(snacks)):
    item = snacks[i]
    print('#%d: %s has %d calories' % (i + 1, item[0], item[1]))

count = fresh_fruit.get('banana', 0)
if count >= 2:
    make_smoothies(count)