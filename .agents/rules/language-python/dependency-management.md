---
description: Managing Python packages, imports, and external libraries
globs: requirements.txt, pyproject.toml, *.py
---
# Dependency Management Standards

## 🎯 Directives
- ALWAYS pin external package dependencies to specific versions to ensure reproducibility.
- ALWAYS use isolated virtual environments (`venv`, `poetry`, `uv`) to prevent dependency conflicts.
- ALWAYS use `pdm config use_uv true` when using PDM to leverage uv for faster dependency resolution and installation.
- ALWAYS actively prevent circular physical dependencies. If A imports B and B imports A, extract shared logic to a lower-level module or use Dependency Inversion.
- ALWAYS use dynamic imports (importing inside a function) ONLY as a last resort to break unavoidable circular dependencies.
- ALWAYS encapsulate external libraries with proprietary API wrappers. Do not let third-party library objects leak deep into the core domain logic.
- ALWAYS evaluate external dependencies against safety criteria: Python 3 compatibility, active maintenance, license compatibility.
- ALWAYS prefer the Python Standard Library over external dependencies for basic utilities (`itertools`, `collections`, `datetime`, `argparse`).
- ALWAYS use `stevedore` or `setuptools` entry points when building plug-in architectures to dynamically load extensions.
- ALWAYS use PEP 440 compliant version numbering (e.g., `1.2.0`, `2.3.1b2`).
- ALWAYS use declarative configuration (`setup.cfg` or `pyproject.toml`) for package metadata instead of complex `setup.py` scripts.

## 📝 Examples

### ✅ DO
```python
# db_wrapper.py
import external_orm_library

class DatabaseAPI:
    def get_user(self, user_id: int) -> dict:
        return external_orm_library.fetch(user_id)
```

### ❌ DON'T
```python
# business_logic.py
import external_orm_library # Leaking external dependency into core logic

def process_user(user_id: int):
    user = external_orm_library.fetch(user_id)