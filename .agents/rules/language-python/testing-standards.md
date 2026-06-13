---
description: TDD, pytest, mocking, and test architecture
globs: test_*.py, *_test.py
---
# Testing Standards

## 🎯 Directives
- ALWAYS follow Double-Loop Test-Driven Development (TDD): Use an outer loop of Functional Tests (FTs) to drive high-level requirements, and an inner loop of Unit Tests (Red, Green, Refactor) to drive implementation details.
- ALWAYS use High Gear vs Low Gear TDD: Write the bulk of your tests against the Service Layer (edge-to-edge) using primitives and fakes to decouple tests from domain implementation details. Maintain a small core of tests against the Domain Model for complex logic.
- ALWAYS structure tests using the AAA pattern (Arrange, Act, Assert) or Given-When-Then. Keep the Act phase to 1-2 lines.
- ALWAYS ensure each test tests exactly one thing (single concept or behavior per test) to isolate failures.
- ALWAYS test behavior, not implementation. NEVER test constants (e.g., exact HTML strings); use structural checks (e.g., `assertTemplateUsed`) instead.
- ALWAYS use Triangulation to drive out generic implementations: if a test allows a "cheating" hardcoded implementation, write another test to force the correct logic.
- ALWAYS apply the "Three Strikes and Refactor" rule to eliminate duplication in test code.
- ALWAYS use `pytest` as the primary test runner and `pytest-cov` for coverage.
- ALWAYS use `pytest` fixtures with `yield` for setup and guaranteed teardown (Annihilate).
- ALWAYS use parameterized fixtures (`@pytest.fixture(params=[...])`) to run the same test scenarios against different drivers or configurations.
- ALWAYS run tests in parallel using `pytest-xdist` (e.g., `pytest -n auto`) to speed up large test suites.
- ALWAYS isolate tests. Tests MUST NOT depend on the state of other tests.
- ALWAYS use `@mock.patch` on the *target namespace* (where the dependency is used), not where it is defined.
- ALWAYS pass `spec=True` or the target class to `mock.patch` to prevent silent typos in mock assertions.
- NEVER mock internal application dependencies or ORM sessions; ALWAYS use Dependency Injection and in-memory Fakes (e.g., `FakeRepository`, `FakeUnitOfWork`). Follow the "Don't mock what you don't own" principle.
- ALWAYS use `django.test.LiveServerTestCase` for Functional Tests. NEVER use `time.sleep()`; ALWAYS implement explicit polling/wait loops.
- ALWAYS use `hypothesis` for Property-Based Testing to generate edge cases and test invariants.
- ALWAYS use `mutmut` for Mutation Testing to verify the actual robustness of the test suite, not just line coverage.
- ALWAYS use `behave` and Gherkin (`.feature` files) for Acceptance Testing and BDD.
- ALWAYS use `repr` strings for debugging output.
- ALWAYS verify related behaviors in `TestCase` subclasses.
- ALWAYS isolate tests from each other with `setUp`, `tearDown`, `setUpModule`, and `tearDownModule`.
- ALWAYS encapsulate dependencies to facilitate mocking and testing.
- ALWAYS consider interactive debugging with `pdb`.
- ALWAYS structure the `tests/` directory to separate unit, integration, e2e, and performance tests, mirroring the `src/` directory for unit tests.
- ALWAYS mirror the structure of the rest of the source tree within the `tests` directory (e.g., code in `src/app/services/auth.py` MUST be tested in `tests/unit/app/services/test_auth.py`).
- ALWAYS ensure tests are stored inside a `tests` subpackage of your application/library so they can be shipped and reused, and to prevent them from being accidentally installed as a top-level `tests` module.

## 📁 Test Directory Structure
```text
my-python-project/
├── src/                        # Source code
│   └── app/
│       ├── services/
│       │   └── auth.py
│       └── utils/
│           └── logger.py
├── tests/
│   ├── conftest.py             # Root fixtures (Shared API clients, DB engine)
│   ├── unit/                   # 1-to-1 Mirror of src/
│   │   └── app/
│   │       ├── services/
│   │       │   ├── test_auth.py
│   │       │   └── mocks.py        # Complex mock objects for unit level
│   │       └── utils/
│   │           └── test_logger.py
│   ├── integration/
│   │   ├── internal/           # Testing logic + DB (Postgres/Redis)
│   │   │   ├── conftest.py     # DB-specific fixtures (Transaction rollback)
│   │   │   └── test_user_db.py
│   │   └── external/           # External API (Sandbox/Live)
│   │       ├── cassettes/      # VCR.py YAML recordings
│   │       │   └── test_stripe_pay.yaml
│   │       ├── conftest.py     # External auth / VCR config
│   │       └── test_stripe.py
│   ├── e2e/                    # Playwright (Python version)
│   │   ├── test_ui_flow.py
│   │   └── pom/                # Page Object Models
│   │       └── dashboard_page.py
│   ├── performance/            # Locust testing
│   │   └── locustfile.py
│   └── data/                   # GLOBAL STATIC FIXTURES (The Python way)
│       ├── sample_payload.json
│       └── test_avatar.png
├── pytest.ini                  # Defines markers like [external, smoke]
└── pyproject.toml
```

##  Examples

### ✅ DO
```python
import pytest
from unittest.mock import patch, call

@pytest.fixture
def db_session():
    db = setup_db()
    yield db
    db.teardown()

@patch("app.services.send_email", spec=True)
def test_user_registration_sends_email(mock_send_email, db_session):
    # Arrange
    user_data = {"email": "test@example.com"}
    
    # Act
    register_user(user_data, db_session)
    
    # Assert
    assert mock_send_email.call_args == call("test@example.com", "Welcome!")
```

### ❌ DON'T
```python
def test_user_registration():
    # Missing isolation, manual teardown, no spec on mock
    db = setup_db()
    with patch("app.email_module.send_email") as mock_send:
        register_user({"email": "test@example.com"}, db)
        mock_send.assert_called_with("test@example.com", "Welcome!")
    db.teardown() # Skipped if assert fails