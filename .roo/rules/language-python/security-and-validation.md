---
description: Data validation, security scanning, and safe parsing
globs: *.py
---
# Security and Validation Standards

## 🎯 Directives
- ALWAYS use `pydantic` for runtime validation of external or dynamic data (e.g., JSON, YAML, API payloads).
- ALWAYS use `pandera` to validate Pandas/Polars dataframe schemas at runtime.
- ALWAYS enforce data integrity constraints at the lowest possible level (e.g., database `UNIQUE`, `NOT NULL`, `CHECK` constraints).
- ALWAYS use `ast.literal_eval()` instead of `eval()` for evaluating strings containing Python literals.
- ALWAYS use `yaml.safe_load()` instead of `yaml.load()` to prevent arbitrary code execution.
- ALWAYS use parameterized queries or ORMs to prevent SQL injection. NEVER use f-strings or string concatenation for SQL queries.
- ALWAYS include CSRF tokens (`{% csrf_token %}`) in Django POST forms.
- ALWAYS use `bandit` in CI/CD pipelines to scan for common security vulnerabilities.
- ALWAYS use `dodgy` or similar tools to scan for hardcoded secrets or credentials.
- ALWAYS escape HTML characters in tests when asserting against rendered templates (e.g., `django.utils.html.escape`).

## 📝 Examples

### ✅ DO
```python
from pydantic.dataclasses import dataclass
from pydantic import PositiveInt, constr

@dataclass
class UserProfile:
    username: constr(min_length=3, max_length=30)
    age: PositiveInt

# Safe SQL execution
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

### ❌ DON'T
```python
class UserProfile:
    def __init__(self, username: str, age: int):
        self.username = username
        self.age = age # No runtime validation

# SQL Injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")