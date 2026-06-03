---
description: Docstrings, comments, and API documentation
globs: *.py
---
# Documentation and Comments Standards

## 🎯 Directives
- ALWAYS write PEP 257 compliant docstrings for EVERY module, class, and public function/method.
- ALWAYS ensure the first line of a docstring is a concise summary. Subsequent paragraphs MUST detail arguments, return values, and raised exceptions.
- ALWAYS document class invariants explicitly in the class-level docstring.
- ALWAYS use Sphinx, `autodoc`, and `autosummary` for generating project documentation from reST (`.rst`) files.
- ALWAYS embed interactive Python examples starting with `>>>` in docstrings to utilize the `doctest` module.
- ALWAYS use the `warnings` module (`warnings.warn`) with `DeprecationWarning` and an appropriate `stacklevel` (e.g., 2 or 3) when deprecating APIs.
- ALWAYS use the `.. deprecated:: <version>` Sphinx directive in docstrings for deprecated elements.
- ALWAYS document API changes thoroughly, including new elements, deprecated elements, and explicit migration instructions.
- ALWAYS consider using libraries like `debtcollector` to automate deprecation warnings and docstring updates.
- NEVER duplicate type information in the docstring if it is already provided via `typing` annotations in the function signature.
- NEVER write comments that merely repeat what the code is doing. Comments MUST explain the *why* or the business context.

## 📝 Examples

### ✅ DO
```python
import warnings

def calculate_velocity(distance: float, time: float) -> float:
    """Calculate velocity given distance and time.
    
    >>> calculate_velocity(100.0, 2.0)
    50.0
    """
    if time <= 0:
        raise ValueError("Time must be positive")
    return distance / time

def old_calculate(d: float, t: float) -> float:
    """
    .. deprecated:: 2.0
       Use :func:`calculate_velocity` instead.
    """
    warnings.warn("old_calculate is deprecated", DeprecationWarning, stacklevel=2)
    return calculate_velocity(d, t)
```

### ❌ DON'T
```python
def calc(d, t):
    # divide d by t
    return d / t