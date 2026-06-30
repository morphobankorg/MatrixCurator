# Rules

## language-python

### Anti-Patterns Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ❌ DON'T
```python
def add_item(item, items=[]):
    items.append(item)
    return items
```

##### ✅ DO
```python
def add_item(item, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

### Architecture and Structure Standards

#### 🎯 Directives
- ALWAYS follow the standard FastAPI project structure with separated `api`, `core`, `database`, `services`, `repositories`, `utils`, and `schemas` directories, or use a modular `src/modules` layout.
- ALWAYS separate domain logic from infrastructure concerns (Domain-Driven Design).
- ALWAYS distinguish between Entities (identity equality, mutable) and Value Objects (value equality, immutable).
- ALWAYS use `@dataclass(frozen=True)` for Value Objects.
- ALWAYS implement `__eq__` and `__hash__` for Entities based on their unique reference/identity, not their attributes.
- ALWAYS use Domain Service functions for business logic that doesn't naturally fit inside a single Entity or Value Object.
- ALWAYS use the Repository Pattern to abstract data access. Repositories MUST only return and accept Aggregate Roots.
- ALWAYS use the Unit of Work (UoW) pattern to abstract atomic operations. Use context managers (`with uow:`).
- ALWAYS require explicit commits (`uow.commit()`) and rollback by default on exceptions or early exits.
- ALWAYS encapsulate use cases in a Service Layer. Service functions MUST accept primitive types, not domain objects.
- ALWAYS use a Message Bus to route Commands (1:1 routing) and Events (1:N routing).
- ALWAYS separate read operations from write operations (CQRS). Use raw SQL or denormalized views for read models.
- ALWAYS decouple microservices using Event-Driven Architecture and message brokers (e.g., Redis, Kafka).
- ALWAYS compose classes instead of nesting many levels of built-in types (e.g., dict of dicts).
- ALWAYS accept functions instead of classes for simple interfaces (e.g., using `__call__` or passing a callable).
- ALWAYS use `@classmethod` polymorphism to construct objects generically instead of `__init__` overloading.
- ALWAYS inherit from `collections.abc` for custom container types to ensure all required methods are implemented.
- ALWAYS use packages to organize modules and provide stable APIs (using `__all__` in `__init__.py`).
- ALWAYS apply the Functional Core, Imperative Shell pattern: pure functions for business logic, imperative shell for I/O and state.
- ALWAYS use Dependency Injection. Pass dependencies explicitly to handlers/services.
- ALWAYS centralize dependency wiring in a Composition Root (e.g., `bootstrap.py`).
- ALWAYS use `mkinit` to automatically generate `__init__.py` files.
- ALWAYS define `__all__` in your modules to explicitly declare public APIs for `mkinit` to pick up.
- ALWAYS redirect after a POST request (Post/Redirect/Get pattern) to prevent duplicate submissions.
- ALWAYS follow YAGNI (You Aren't Gonna Need It) and build the Minimum Viable App first. Do not add features or infrastructure until tests demand them.
- ALWAYS apply the "Unicode Sandwich" pattern for text processing: decode bytes to `str` as early as possible on input, process exclusively with `str`, and encode to bytes as late as possible on output.
- ALWAYS use a proxy/load-balancer (e.g., NGINX, Traefik) in front of ASGI/WSGI servers to handle static assets and use a CDN when possible.
- ALWAYS subclass `collections.UserDict`, `collections.UserList`, or `collections.UserString` when extending built-in collections. NEVER subclass `dict`, `list`, or `str` directly, as their C implementations bypass overridden methods.
- ALWAYS organize code based on features, not on types. NEVER create modules like `exceptions.py` or `functions.py` that group code by type.
- ALWAYS isolate ORM libraries in a specific storage module (e.g., `myapp.storage`) to easily swap them out and prevent ORM objects from leaking.
- ALWAYS rely on RDBMS constraints (e.g., `UNIQUE`) and catch the resulting exceptions (e.g., `UniqueViolationError`) instead of performing a `SELECT` followed by an `INSERT` to prevent race conditions.
- NEVER place database queries, orchestration logic, or domain rules inside API endpoints (e.g., Flask/Django views).
- NEVER allow the Domain Model to import or invoke infrastructure code (e.g., ORMs, email clients).
- NEVER couple Domain Models to ORM classes (e.g., inheriting from `db.Model` or `Base`). ALWAYS use classical mapping or separate ORM models to ensure the ORM depends on the model, not the other way around.

#### 📝 Examples

##### ✅ DO
```python
def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        batchref = product.allocate(line)
        uow.commit()
    return batchref
```

```text
project_name/
├── requirements.txt       # Python dependencies
├── Dockerfile.txt         # Docker containerfile
├── README.md              # Project documentation
├── .gitignore             # Define what to ignore during version control
├── src/                   # Source code directory
│   ├── main.py            # Entry point for your FastAPI application
│   ├── __init__.py        # Initialize the src package
│   ├── api/               # API endpoints
│   │   ├── __init__.py    # Initialize the api package
│   │   ├── v1/            # Versioned API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py  # Define API routes and handlers
│   │   │   └── dependencies.py # Dependency injection
│   ├── config/            # Application configurations
│   │   ├── __init__.py
│   │   └── main.py        # Pydantic settings
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py    # Security related utilities
│   ├── database/          # Database related files
│   │   ├── __init__.py
│   │   ├── session.py     # Database session handling
│   │   └── migrations/    # Database migrations
│   ├── services/          # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py # Example service
│   ├── repositories/      # Database logic layer
│   │   ├── __init__.py
│   │   ├── user_repository.py # Example repository
│   ├── utils/             # Utility functions
│   │   ├── __init__.py
│   │   └── logging.py     # Logging configuration
│   └── schemas/           # Pydantic schemas
│       ├── __init__.py
│       ├── pydantic_schema.py
```

Or using a modular `src` layout:

```text
project_name/
├── requirements.txt       # Python dependencies
├── Dockerfile.txt         # Docker containerfile
├── README.md              # Project documentation
├── .gitignore             # Define what to ignore during version control
├── src/                   # Source code directory
│   ├── main.py            # Entry point for your FastAPI application
│   ├── config/            # Application configurations
│   │   ├── __init__.py
│   │   └── main.py        # Pydantic settings
│   ├── core/              # Core functionality (security, etc.)
│   │   ├── __init__.py
│   │   └── security.py
│   ├── utils/             # Utility functions
│   │   ├── __init__.py
│   │   └── logging.py     # Logging configuration
│   └── modules/           # Feature-based modules
│       ├── __init__.py
│       └── users/         # Example module
│           ├── __init__.py
│           ├── router.py  # API endpoints for users
│           ├── schemas.py # Pydantic schemas
│           ├── models.py  # ORM models
│           ├── service.py # Business logic
│           └── repository/ # Database access
│               ├── __init__.py
│               └── user.py
```

##### ❌ DON'T
```python
@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    session = get_session()
    batches = session.query(Batch).all()
    line = OrderLine(request.json['orderid'], request.json['sku'], request.json['qty'])
    model.allocate(line, batches)
    session.commit()
    return jsonify({'status': 'ok'})
```

### Code Style and Formatting Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
```python
for rank, (name, calories) in enumerate(snacks, 1):
    print(f'#{rank}: {name} has {calories} calories')

if (count := fresh_fruit.get('banana', 0)) >= 2:
    make_smoothies(count)
```

##### ❌ DON'T
```python
for i in range(len(snacks)):
    item = snacks[i]
    print('#%d: %s has %d calories' % (i + 1, item[0], item[1]))

count = fresh_fruit.get('banana', 0)
if count >= 2:
    make_smoothies(count)
```

### Configuration and Environment Standards

#### 🎯 Directives
- ALWAYS follow the 12-Factor App methodology: store configuration that varies between environments in environment variables.
- ALWAYS implement "fail hard" logic for secrets in production. Raise `KeyError` if a required secret is missing when `DEBUG=False`.
- ALWAYS use a `requirements.txt` (or `pyproject.toml`/`uv.lock`) to explicitly declare production dependencies.
- ALWAYS separate development/testing dependencies from production dependencies.
- ALWAYS use Docker for containerization to ensure reproducible environments.
- ALWAYS use lightweight base images (e.g., `python:3.12-slim`).
- ALWAYS run applications as a nonroot user inside Docker containers.
- ALWAYS use bind mounts (`--mount type=bind`) for stateful data (like SQLite databases) and ensure host file permissions match the container's nonroot UID.
- ALWAYS use a production-ready WSGI/ASGI server (e.g., Gunicorn, Uvicorn) in Docker. NEVER use development servers (e.g., Django's `runserver`) in production.
- ALWAYS configure logging to output to the console (`StreamHandler`) so Docker can capture tracebacks.
- ALWAYS use `WhiteNoise` or a reverse proxy (Nginx) to serve static files in production.
- ALWAYS use declarative Infrastructure as Code (IaC) tools like Ansible for server provisioning and deployment.

#### 📝 Examples

##### ✅ DO
```python
import os

if "DJANGO_DEBUG_FALSE" in os.environ:
    DEBUG = False
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
    ALLOWED_HOSTS = [os.environ["DJANGO_ALLOWED_HOST"]]
else:
    DEBUG = True
    SECRET_KEY = "dev-secret-key"
    ALLOWED_HOSTS = []
```

##### ❌ DON'T
```python
### Fails silently and runs insecurely in production
DEBUG = os.environ.get("DEBUG", False)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
```

### Dependency Management Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
```python
### db_wrapper.py
import external_orm_library

class DatabaseAPI:
    def get_user(self, user_id: int) -> dict:
        return external_orm_library.fetch(user_id)
```

##### ❌ DON'T
```python
### business_logic.py
import external_orm_library # Leaking external dependency into core logic

def process_user(user_id: int):
    user = external_orm_library.fetch(user_id)
```

### Documentation and Comments Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
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

##### ❌ DON'T
```python
def calc(d, t):
    # divide d by t
    return d / t
```

### Error Handling Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
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

##### ❌ DON'T
```python
def process_data(data: str):
    try:
        parsed = parse_json(data)
        return enrich_data(parsed)
    except Exception:
        return None # Silent failure, returns None
```

### Logging and Observability Standards

#### 🎯 Directives
- ALWAYS use the standard `logging` module. NEVER use `print()` for application logs in production code.
- ALWAYS use `logging.exception("message")` inside `except` blocks to automatically log the full stack trace of the caught exception.
- ALWAYS configure a `StreamHandler` outputting to the console (stdout/stderr) in containerized environments (Docker) so logs are captured by the container runtime.
- ALWAYS inject debug log statements immediately before invoking handlers in a Message Bus or Event-Driven Architecture (e.g., `logger.debug('handling event %s', event)`).
- ALWAYS use structured logging or include contextual identifiers (e.g., `order_id`, `user_id`) in log messages to facilitate tracing across distributed systems.
- ALWAYS configure appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Use `INFO` for normal operational milestones and `DEBUG` for detailed tracing.
- ALWAYS capture warnings in the logging system using `logging.captureWarnings(True)` in production configurations.

#### 📝 Examples

##### ✅ DO
```python
import logging

logger = logging.getLogger(__name__)

def process_payment(order_id: str, amount: float) -> None:
    logger.info("Processing payment for order %s: $%.2f", order_id, amount)
    try:
        charge_card(amount)
    except PaymentGatewayError:
        logger.exception("Payment failed for order %s", order_id)
        raise
```

##### ❌ DON'T
```python
def process_payment(order_id: str, amount: float) -> None:
    print(f"Processing payment for {order_id}")
    try:
        charge_card(amount)
    except PaymentGatewayError as e:
        print(f"Error: {e}") # Loses the stack trace
```

### Naming Conventions Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
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

##### ❌ DON'T
```python
MaxRetries = 3

class order_processor:
    def ProcessOrder(self, OrderId: str):
        pass

@dataclass
class CreateOrderEvent(Event): # Imperative mood for an event
    order_id: str
```

### Performance and Optimization Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
```python
import collections

queue = collections.deque()
queue.append(item)
processed = queue.popleft() # O(1)
```

##### ❌ DON'T
```python
queue = []
queue.append(item)
processed = queue.pop(0) # O(N)
```

##### ✅ DO
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

##### ❌ DON'T
```python
### Global scope loop is slow due to LOAD_GLOBAL
result = ""
valid_items = ["apple", "banana", "orange"] # O(N) lookup

for item in items:
    if item in valid_items:
        result += item # Quadratic memory reallocation
```

### Security and Validation Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
```python
from pydantic.dataclasses import dataclass
from pydantic import PositiveInt, constr

@dataclass
class UserProfile:
    username: constr(min_length=3, max_length=30)
    age: PositiveInt

### Safe SQL execution
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

##### ❌ DON'T
```python
class UserProfile:
    def __init__(self, username: str, age: int):
        self.username = username
        self.age = age # No runtime validation

### SQL Injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### Testing Standards

#### 🎯 Directives
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

#### 📁 Test Directory Structure
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

####  Examples

##### ✅ DO
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

##### ❌ DON'T
```python
def test_user_registration():
    # Missing isolation, manual teardown, no spec on mock
    db = setup_db()
    with patch("app.email_module.send_email") as mock_send:
        register_user({"email": "test@example.com"}, db)
        mock_send.assert_called_with("test@example.com", "Welcome!")
    db.teardown() # Skipped if assert fails
```

### Type Safety Standards

#### 🎯 Directives
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

#### 📝 Examples

##### ✅ DO
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

##### ❌ DON'T
```python
from typing import Any

### Missing return type, implicit None, uses Any, tightly coupled to concrete class
def notify_user(user_id, sender: Any):
    if user_id < 0:
        return None
    sender.send("user@example.com", "Hello")
    return "Success"
```
# Repository Map

```python

.agents\memory.json

.agents\rules\language-python\anti-patterns.md

.agents\rules\language-python\architecture-and-structure.md

.agents\rules\language-python\code-style-and-formatting.md

.agents\rules\language-python\configuration-and-environment.md

.agents\rules\language-python\dependency-management.md

.agents\rules\language-python\documentation-and-comments.md

.agents\rules\language-python\error-handling.md

.agents\rules\language-python\logging-and-observability.md

.agents\rules\language-python\naming-conventions.md

.agents\rules\language-python\performance-and-optimization.md

.agents\rules\language-python\security-and-validation.md

.agents\rules\language-python\testing-standards.md

.agents\rules\language-python\type-safety.md

.agents\skills\docling\SKILL.md

.agents\skills\dspy\SKILL.md

.agents\skills\langchain\SKILL.md

.agents\skills\langfuse\SKILL.md

.agents\skills\langgraph\SKILL.md

.agents\skills\litellm\SKILL.md

.devcontainer\devcontainer.json

.dockerignore

.env.example

.github\pull_request_template.md

.rune\config

.runemodules

.streamlit\secrets_template.toml

AGENTS.md

Dockerfile

LICENSE

README.md

ROADMAP.md

apps\matrixcurator-api\pdm.lock

apps\matrixcurator-api\pyproject.toml

apps\matrixcurator-api\src\__init__.py

apps\matrixcurator-api\src\dependencies.py:
⋮
│def get_client() -> MatrixCuratorClient:
⋮

apps\matrixcurator-api\src\main.py:
⋮
│@app.on_event("startup")
│async def startup_event():
⋮
│@app.get("/health")
│async def health_check():
⋮

apps\matrixcurator-api\src\routers\agent.py:
⋮
│@router.post("/extract", response_model=ExtractResponse)
│async def extract_data(
│    request: ExtractRequest, client: MatrixCuratorClient = Depends(get_client)
⋮

apps\matrixcurator-api\src\routers\document.py:
⋮
│@router.post("/parse", response_model=ParseResponse)
│async def parse_document_endpoint(
│    file: UploadFile = File(...), client: MatrixCuratorClient = Depends(get_client)
⋮
│@router.post("/nexus", response_model=NexusGenerateResponse)
│async def generate_nexus_endpoint(
│    request: NexusGenerateRequest, client: MatrixCuratorClient = Depends(get_client)
⋮

apps\matrixcurator-api\tests\integration\test_agent_routes.py:
⋮
│def test_extract_data_success():
⋮
│def test_extract_data_failure():
⋮
│def test_extract_data_validation_error():
⋮

apps\matrixcurator-api\tests\integration\test_document_routes.py:
⋮
│@pytest.fixture
│def sample_nexus():
⋮
│def test_parse_document_txt():
⋮
│def test_parse_document_unsupported():
⋮
│def test_generate_nexus(sample_nexus):
⋮
│def test_generate_nexus_invalid_payload():
⋮

apps\matrixcurator-ui\pyproject.toml

apps\matrixcurator-ui\src\main.py

apps\matrixcurator-ui\tests\test_app.py:
⋮
│@pytest.fixture
│def app():
⋮
│@patch("apps.streamlit.src.main.client.parse_document")
│def test_parse_document_success(mock_parse, app):
⋮

benchmark_out.txt

output.txt

packages.txt

packages\matrixcurator\pyproject.toml

packages\matrixcurator\src\matrixcurator\__init__.py

packages\matrixcurator\src\matrixcurator\client.py:
⋮
│class MatrixCuratorClient:
│    def __init__(self, app_name: str = "matrixcurator", **kwargs: Any):
│        if kwargs:
│            new_settings = Settings(**kwargs)
│            for key, value in new_settings.model_dump(exclude_unset=True).items():
│                setattr(global_settings, key, value)
│
│        self.logger = structlog.get_logger(__name__)
⋮
│    def parse_document(self, content: bytes, filename: str) -> str:
⋮
│    async def extract_characters(
│        self,
│        context: str,
│        character_indices: List[int],
│        starting_tier: int = 2,
│        user_id: Optional[str] = None,
⋮
│    def generate_nexus(
│        self, original_nexus: str, extracted_states: List[Dict[str, Any]]
⋮

packages\matrixcurator\src\matrixcurator\config\__init__.py

packages\matrixcurator\src\matrixcurator\config\main.py:
⋮
│class ContextStrategy(str, Enum):
⋮
│class OrchestrationStrategy(str, Enum):
⋮
│class IntelligenceStrategy(str, Enum):
⋮
│class Settings(LoggingSettings):
│    model_config = SettingsConfigDict(
│        env_file=".env", env_file_encoding="utf-8", extra="ignore"
⋮
│    @property
│    def current_context_strategy(self) -> ContextStrategy:
⋮
│    @property
│    def current_orchestration_strategy(self) -> OrchestrationStrategy:
⋮
│    @property
│    def current_intelligence_strategy(self) -> IntelligenceStrategy:
⋮
│    def get_model_for_tier(self, requested_tier: int) -> str:
⋮

packages\matrixcurator\src\matrixcurator\data.sqlite

packages\matrixcurator\src\matrixcurator\exceptions.py:
⋮
│class MatrixCuratorError(Exception):
⋮
│class DocumentParseError(MatrixCuratorError):
⋮
│class NexusFormatError(MatrixCuratorError):
⋮
│class LLMServiceError(MatrixCuratorError):
⋮
│class ContextLengthExceededError(MatrixCuratorError):
⋮

packages\matrixcurator\src\matrixcurator\integrations\__init__.py

packages\matrixcurator\src\matrixcurator\integrations\docling.py:
⋮
│class McpVlmEngine(ApiVlmEngine):
│    """
│    Custom VLM Engine for Docling that intercepts calls for MCP sampling.
│    Falls back to litellm.completion (Gemini) if no MCP session is active or if sampling fails.
⋮
│    def predict_batch(self, input_batch: List[VlmEngineInput]) -> List[VlmEngineOutput]:
⋮
│class McpVlmConvertModel(VlmConvertModel):
│    """
│    Custom VlmConvertModel that injects McpVlmEngine.
⋮
│    def __init__(self, *args, **kwargs):
⋮
│class McpVlmPipeline(VlmPipeline):
│    """
│    Custom VlmPipeline that uses McpVlmConvertModel.
⋮
│    def _initialize_new_runtime_system(
│        self, pipeline_options: VlmPipelineOptions
⋮

packages\matrixcurator\src\matrixcurator\integrations\dspy.py:
⋮
│class MCPAwareLM(dspy.LM):
│    """
│    Custom DSPy LM that intercepts calls for MCP sampling.
│    Falls back to native dspy.LM (LiteLLM) if no MCP session is active or if sampling fails.
⋮
│    def forward(
│        self,
│        prompt: Optional[str] = None,
│        messages: Optional[List[Dict[str, Any]]] = None,
│        **kwargs,
⋮
│    async def aforward(
│        self,
│        prompt: Optional[str] = None,
│        messages: Optional[List[Dict[str, Any]]] = None,
│        **kwargs,
⋮
│def configure_dspy(model_name: Optional[str] = None):
⋮
│class CharacterExtraction(dspy.Signature):
⋮
│class ExtractionEvaluation(dspy.Signature):
⋮
│class ExtractionModule(dspy.Module):
│    def __init__(self):
│        super().__init__()
│        self.extract = dspy.ChainOfThought(CharacterExtraction)
│
│        # Try to load compiled weights if they exist
│        weights_path = os.path.join(
│            os.path.dirname(__file__), "..", "weights", "gemini-1.5-pro.json"
│        )
│        if os.path.exists(weights_path):
│            try:
⋮
│    def forward(
│        self,
│        document_text: str,
│        character_index: int,
│        previous_errors: Optional[str] = None,
⋮
│class EvaluationModule(dspy.Module):
│    def __init__(self):
│        super().__init__()
│        self.evaluate = dspy.ChainOfThought(ExtractionEvaluation)
│
│        # Try to load compiled weights if they exist
│        weights_path = os.path.join(
│            os.path.dirname(__file__), "..", "weights", "gemini-1.5-pro.json"
│        )
│        if os.path.exists(weights_path):
│            try:
⋮
│    def forward(self, document_text: str, extracted_data: Dict[str, Any]):
⋮

packages\matrixcurator\src\matrixcurator\integrations\litellm.py:
⋮
│def _format_mcp_to_litellm(mcp_result: Any, model: str) -> ModelResponse:
⋮
│async def acompletion(*args, **kwargs) -> ModelResponse:
⋮
│def completion(*args, **kwargs) -> ModelResponse:
⋮

packages\matrixcurator\src\matrixcurator\integrations\mcp.py:
⋮
│class MCPSamplingError(Exception):
⋮
│async def sample_message(
│    session: Any,
│    messages: List[Dict[str, Any]],
│    model_preferences: Optional[Dict[str, Any]] = None,
│    system_prompt: Optional[str] = None,
│    include_context: Optional[str] = None,
│    temperature: Optional[float] = None,
│    max_tokens: Optional[int] = None,
⋮

packages\matrixcurator\src\matrixcurator\integrations\prompts.py:
⋮
│class StateModel(BaseModel):
⋮
│class CharacterModel(BaseModel):
⋮
│class CharacterStateModel(BaseModel):
⋮
│class ExtractionResult(BaseModel):
⋮
│async def extract_characters_and_states(
│    text: str, indices: Optional[List[int]] = None
⋮

packages\matrixcurator\src\matrixcurator\integrations\supabase.py:
⋮
│def get_supabase_client() -> Client:
⋮
│def get_client() -> Client:
⋮

packages\matrixcurator\src\matrixcurator\modules\__init__.py

packages\matrixcurator\src\matrixcurator\modules\agent\graph.py:
⋮
│def build_graph():
⋮

packages\matrixcurator\src\matrixcurator\modules\agent\memory.py:
⋮
│def get_store():
⋮

packages\matrixcurator\src\matrixcurator\modules\agent\nodes.py:
⋮
│class CharacterStateOutput(BaseModel):
⋮
│def llm_error_handler(state: AgentState, error: Exception) -> Command:
⋮
│def extractor_agent(state: AgentState) -> Dict[str, Any]:
⋮
│def evaluator_agent(state: AgentState) -> Dict[str, Any]:
⋮
│def supervisor_node(state: AgentState) -> Command:
⋮

packages\matrixcurator\src\matrixcurator\modules\agent\schemas.py:
⋮
│class ExtractRequest(BaseModel):
⋮
│class ExtractResponse(BaseModel):
⋮

packages\matrixcurator\src\matrixcurator\modules\agent\state.py:
⋮
│@dataclass
│class ContextSchema:
⋮
│class AgentState(MessagesState):
⋮

packages\matrixcurator\src\matrixcurator\modules\document\repositories\docx.py:
⋮
│def read_docx(file_content: bytes, **kwargs) -> str:
⋮

packages\matrixcurator\src\matrixcurator\modules\document\repositories\nexus.py:
⋮
│def read_nexus(file_content: bytes, **kwargs) -> str:
⋮
│def write_nexus(
│    original_nexus: str, extracted_states: List[Dict[str, Any]], **kwargs
⋮

packages\matrixcurator\src\matrixcurator\modules\document\repositories\pdf.py:
⋮
│def read_pdf(file_content: bytes, **kwargs) -> str:
⋮

packages\matrixcurator\src\matrixcurator\modules\document\repositories\txt.py:
⋮
│def read_txt(file_content: bytes, **kwargs) -> str:
⋮

packages\matrixcurator\src\matrixcurator\modules\document\schemas.py:
⋮
│class ParseResponse(BaseModel):
⋮
│class NexusGenerateRequest(BaseModel):
⋮
│class NexusGenerateResponse(BaseModel):
⋮

packages\matrixcurator\src\matrixcurator\modules\document\services.py:
⋮
│def parse_document(file_content: bytes, filename: str, **kwargs) -> str:
⋮
│def generate_document(
│    original_nexus: str, extracted_states: List[Dict[str, Any]], **kwargs
⋮

packages\matrixcurator\src\matrixcurator\modules\graph.py:
⋮
│def build_graph():
⋮

packages\matrixcurator\src\matrixcurator\modules\memory.py:
⋮
│def get_store():
⋮

packages\matrixcurator\src\matrixcurator\modules\nodes.py:
⋮
│class CharacterStateOutput(BaseModel):
⋮
│def llm_error_handler(state: AgentState, error: Exception) -> Command:
⋮
│def extractor_agent(state: AgentState) -> Dict[str, Any]:
⋮
│def evaluator_agent(state: AgentState) -> Dict[str, Any]:
⋮
│def supervisor_node(state: AgentState) -> Command:
⋮

packages\matrixcurator\src\matrixcurator\modules\retrieval\repositories\sqlite.py:
⋮
│def _get_embedding_dimension() -> int:
⋮
│class DocumentChunkMeta(Base):
⋮
│def get_engine():
⋮
│def insert_chunks(chunks: List[DocumentChunk]) -> None:
⋮
│def query_similar_chunks(
│    embedding: List[float],
│    match_threshold: float = 0.7,
│    match_count: int = 5,
│    document_id: Optional[str] = None,
│    parser_name: Optional[str] = None,
⋮

packages\matrixcurator\src\matrixcurator\modules\retrieval\repositories\supabase.py:
⋮
│def insert_chunks(chunks: List[DocumentChunk]) -> None:
⋮
│def query_similar_chunks(
│    embedding: List[float],
│    match_threshold: float = 0.7,
│    match_count: int = 5,
│    document_id: str = None,
│    parser_name: str = None,
⋮

packages\matrixcurator\src\matrixcurator\modules\retrieval\schemas.py:
⋮
│class ChunkMetadata(TypedDict, total=False):
⋮
│class DocumentChunk(TypedDict):
⋮

packages\matrixcurator\src\matrixcurator\modules\retrieval\services.py:
⋮
│@retry(
│    stop=stop_after_attempt(5),
│    wait=wait_exponential(multiplier=1, min=2, max=15),
│    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
│)
│async def _fetch_embeddings_with_retry(texts: list[str]):
⋮
│def _get_insert_chunks():
⋮
│def _get_query_similar_chunks():
⋮
│def chunk_text(
│    text: str,
│    document_id: str,
│    chunk_size: int = 1000,
│    chunk_overlap: int = 200,
│    parser_name: Optional[str] = None,
⋮
│async def embed_and_store_chunks(chunks: List[DocumentChunk]) -> None:
⋮
│async def retrieve_context(
│    query: str,
│    match_count: int = 5,
│    document_id: Optional[str] = None,
│    parser_name: Optional[str] = None,
⋮

packages\matrixcurator\src\matrixcurator\modules\schemas.py:
⋮
│class ExtractRequest(BaseModel):
⋮
│class ExtractResponse(BaseModel):
⋮
│class Character(TypedDict):
⋮
│class State(TypedDict):
⋮
│class CharacterState(TypedDict):
⋮
│class Document(TypedDict):
⋮

packages\matrixcurator\src\matrixcurator\modules\state.py:
⋮
│@dataclass
│class ContextSchema:
⋮
│class AgentState(MessagesState):
⋮

packages\matrixcurator\src\matrixcurator\modules\tools\__init__.py

packages\matrixcurator\src\matrixcurator\modules\tools\docling.py:
⋮
│@tool
│def parse_with_docling(
│    file_content: bytes, filename: str, pages: list[int] | None = None
⋮

packages\matrixcurator\src\matrixcurator\modules\tools\docx.py:
⋮
│@tool
│def parse_with_docx(file_content: bytes, filename: str) -> str:
⋮

packages\matrixcurator\src\matrixcurator\modules\tools\pymupdf.py:
⋮
│@tool
│def parse_with_pymupdf(
│    file_content: bytes, filename: str, pages: list[int] | None = None
⋮

packages\matrixcurator\src\matrixcurator\modules\tools\re.py:
⋮
│@tool
│def generate_with_re(
│    original_nexus: str, extracted_states: List[Dict[str, Any]]
⋮

packages\matrixcurator\src\matrixcurator\modules\tools\txt.py:
⋮
│@tool
│def parse_with_txt(file_content: bytes, filename: str) -> str:
⋮

packages\matrixcurator\src\matrixcurator\utils\__init__.py

packages\matrixcurator\src\matrixcurator\utils\concurrency.py:
⋮
│class AsyncRateLimiter:
│    """Rate limiter that restricts execution to a maximum number of calls per time period."""
│
│    def __init__(self, max_calls: int, time_period: float = 1.0) -> None:
⋮
│    async def acquire(self) -> None:
⋮
│class AsyncConcurrencyManager:
│    """Context manager combining asyncio.Semaphore and an optional AsyncRateLimiter."""
│
│    def __init__(
│        self, max_concurrent: int, rate_limiter: Optional[AsyncRateLimiter] = None
⋮
│    async def __aenter__(self) -> "AsyncConcurrencyManager":
⋮
│    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
⋮

packages\matrixcurator\src\matrixcurator\utils\models.py:
⋮
│def get_available_models() -> List[str]:
⋮

packages\matrixcurator\tests\conftest.py:
⋮
│@pytest.fixture
│def sample_nexus():
⋮

packages\matrixcurator\tests\integration\test_docling_pipeline.py:
⋮
│def create_mock_pdf() -> bytes:
⋮
│@patch("matrixcurator.integrations.docling.completion")
│def test_docling_tool_uses_gemini_fallback(mock_completion):
⋮

packages\matrixcurator\tests\integration\test_hitl_workflow.py:
⋮
│@pytest.fixture
│def hitl_graph():
⋮
│@patch("matrixcurator.modules.nodes.parse_document")
⋮
│def test_full_hitl_workflow(mock_eval, mock_extract, mock_discover, mock_parse, hitl_graph):
⋮

packages\matrixcurator\tests\integration\test_strategies.py:
⋮
│@pytest.fixture
│def mock_dspy_extraction():
⋮
│@pytest.fixture
│def mock_litellm_extraction():
⋮
│@pytest.fixture
│def mock_retrieve_context():
⋮
│@pytest.mark.asyncio
│async def test_extraction_node_strategies(mock_dspy_extraction, mock_litellm_extraction, mock_retri
⋮
│def test_evaluation_node_routing_strategies():
⋮

packages\matrixcurator\tests\unit\integrations\test_docling.py:
⋮
│@pytest.fixture
│def mock_mcp_session():
⋮
│@pytest.fixture
│def mock_vlm_input():
⋮
│def test_mcp_vlm_convert_model_forces_api_options():
⋮
│@patch("matrixcurator.integrations.docling.completion")
│def test_mcp_vlm_engine_litellm_fallback(mock_completion, mock_vlm_input):
⋮
│@patch("matrixcurator.integrations.docling.sample_message")
│def test_mcp_vlm_engine_predict_batch_mcp(mock_sample_message, mock_vlm_input, mock_mcp_session):
│    # Arrange
│    options = ApiVlmOptions(url="http://localhost:8000", prompt="test", response_format=ResponseFor
⋮
│    async def mock_sample(*args, **kwargs):
⋮

packages\matrixcurator\tests\unit\integrations\test_dspy.py:
⋮
│@pytest.fixture
│def mock_mcp_session():
⋮
│@patch("matrixcurator.integrations.dspy.DSPyInstrumentor")
│def test_configure_dspy(mock_instrumentor):
⋮
│@pytest.mark.asyncio
│@patch("dspy.LM.aforward")
│async def test_mcp_aware_lm_aforward_with_session(mock_super_aforward, mock_mcp_session):
⋮
│@pytest.mark.asyncio
│@patch("dspy.LM.aforward")
│async def test_mcp_aware_lm_aforward_without_session(mock_super_aforward):
⋮
│@pytest.mark.asyncio
│@patch("dspy.LM.aforward")
│async def test_mcp_aware_lm_aforward_fallback(mock_super_aforward, mock_mcp_session):
⋮

packages\matrixcurator\tests\unit\integrations\test_litellm.py:
⋮
│@pytest.fixture
│def mock_mcp_session():
⋮
│@pytest.mark.asyncio
│@patch("matrixcurator.integrations.litellm.litellm.acompletion")
│async def test_acompletion_with_mcp_session(mock_litellm_acompletion, mock_mcp_session):
⋮
│@pytest.mark.asyncio
│@patch("matrixcurator.integrations.litellm.litellm.acompletion")
│async def test_acompletion_without_mcp_session(mock_litellm_acompletion):
⋮
│@pytest.mark.asyncio
│@patch("matrixcurator.integrations.litellm.litellm.acompletion")
│async def test_acompletion_mcp_fallback(mock_litellm_acompletion, mock_mcp_session):
⋮
│@patch("matrixcurator.integrations.litellm.litellm.completion")
│def test_completion_without_mcp_session(mock_litellm_completion):
⋮

packages\matrixcurator\tests\unit\integrations\test_mcp.py:
⋮
│@pytest.mark.asyncio
│async def test_sample_message_success():
⋮
│@pytest.mark.asyncio
│async def test_sample_message_with_images():
⋮
│@pytest.mark.asyncio
│async def test_sample_message_failure():
⋮

packages\matrixcurator\tests\unit\modules\test_retrieval.py:
⋮
│def test_chunk_text():
⋮
│@pytest.mark.asyncio
⋮
│async def test_embed_and_store_chunks(mock_get_insert, mock_fetch):
⋮
│@pytest.mark.asyncio
⋮
│async def test_retrieve_context(mock_get_query, mock_fetch):
⋮
│@pytest.mark.asyncio
⋮
│async def test_embed_and_store_chunks_batching(mock_sleep, mock_get_insert, mock_fetch):
│    mock_insert = MagicMock()
⋮
│    def side_effect(texts):
⋮
│@pytest.mark.asyncio
⋮
│async def test_embed_and_store_chunks_rate_limit_retry(mock_get_insert, mock_aembedding):
⋮
│@patch('matrixcurator.modules.retrieval.repositories.supabase.get_client')
│def test_insert_chunks_repository(mock_get_client):
⋮
│@patch('matrixcurator.modules.retrieval.repositories.supabase.get_client')
│def test_query_similar_chunks_repository(mock_get_client):
⋮

packages\matrixcurator\tests\unit\modules\test_sqlite_repository.py:
⋮
│@pytest.fixture
│def temp_sqlite_db(tmp_path):
⋮
│def test_insert_and_query_sqlite_vector(temp_sqlite_db):
⋮

packages\matrixcurator\tests\unit\modules\test_tools.py:
⋮
│@patch("matrixcurator.modules.tools.pymupdf.fitz.open")
│def test_pymupdf_tool_success(mock_fitz_open):
⋮
│@patch("matrixcurator.modules.tools.pymupdf.fitz.open")
│def test_pymupdf_tool_page_filtering(mock_fitz_open):
⋮
│@patch("matrixcurator.modules.tools.pymupdf.fitz.open")
│def test_pymupdf_tool_failure(mock_fitz_open):
⋮
│def test_txt_tool_success():
⋮
│def test_re_tool_success():
⋮
│@patch("matrixcurator.modules.tools.docling.DocumentConverter")
│def test_docling_tool_success(mock_converter_class):
⋮
│@patch("matrixcurator.modules.tools.docling.DocumentConverter")
│def test_docling_tool_page_filtering(mock_converter_class):
⋮

packages\matrixcurator\tests\unit\test_client.py:
⋮
│@pytest.fixture
│def client():
⋮
│@patch("matrixcurator.client.parse_document")
│@patch("matrixcurator.client.posthog.capture")
│def test_parse_document(mock_capture, mock_parse, client):
⋮
│@pytest.mark.asyncio
⋮
│async def test_extract_characters_success(mock_capture, mock_ainvoke, client):
⋮
│@patch("matrixcurator.client.generate_document")
│@patch("matrixcurator.client.posthog.capture")
│def test_generate_nexus(mock_capture, mock_generate, client):
⋮

packages\matrixcurator\tests\unit\utils\test_concurrency.py:
⋮
│@pytest.mark.asyncio
│async def test_async_rate_limiter_respects_limit() -> None:
⋮
│@pytest.mark.asyncio
│async def test_async_concurrency_manager_semaphore() -> None:
│    manager = AsyncConcurrencyManager(max_concurrent=1)
│
│    async def worker() -> None:
⋮
│@pytest.mark.asyncio
│async def test_async_concurrency_manager_with_rate_limiter() -> None:
│    limiter = AsyncRateLimiter(max_calls=1, time_period=0.1)
⋮
│    async def worker() -> None:
⋮

pdm.lock

pyproject.toml

pytest.ini

requirements.txt

scripts\__init__.py:
│def lazy_import(module_name, submodules, submod_attrs, eager="auto"):
│    import importlib
⋮
│    def __getattr__(name):
⋮
│def __dir__():
⋮

scripts\compile_weights.py:
⋮
│def extraction_metric(
│    example: dspy.Example, pred: dspy.Prediction, trace=None
⋮
│def load_examples() -> list[dspy.Example]:
⋮
│def main():
⋮

scripts\parse_documents.py:
⋮
│def main() -> None:
│    parser = argparse.ArgumentParser(description="Pre-parse documents for benchmarks")
⋮
│    for idx, row in tqdm(
│        df_docs.iterrows(), total=len(df_docs), desc="Parsing documents"
│    ):
│        existing_text = row.get("text")
⋮
│        def get_existing_page_content(parser_name: str, page_num: int) -> str | None:
⋮

src\benchmark\__init__.py

src\benchmark\__main__.py:
⋮
│def main():
⋮

src\benchmark\agents_benchmark.py:
⋮
│async def agent_task(*, item: Any, df_docs: pd.DataFrame, **kwargs) -> str:
⋮
│def run_agents_benchmark():
│    langfuse, dataset = setup()
│
⋮
│    def process_permutation(routing, intelligence):
⋮

src\benchmark\benchmark_agents.py:
⋮
│@fixture(scope="session")
│def docs_dict(df_docs: pd.DataFrame):
⋮
│@benchmark(dataset_name="character_states")
│@parametrize("routing, intelligence", PERMUTATIONS)
│async def benchmark_agents(
│    dataset_item, routing, intelligence, docs_dict, langfuse_trace
⋮

src\benchmark\benchmark_retrieval.py:
⋮
│async def _execute_retrieval_benchmark(
│    dataset_item: Any,
│    parser_name: str,
│    valid_docs_per_parser: dict[str, set[str] | None],
│    langfuse_trace: Any,
⋮
│@benchmark(dataset_name="character_states")
│async def benchmark_retrieval_docling(
│    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
⋮
│@benchmark(dataset_name="character_states")
│async def benchmark_retrieval_pymupdf(
│    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
⋮
│@benchmark(dataset_name="character_states")
│async def benchmark_retrieval_docx(
│    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
⋮
│@benchmark(dataset_name="character_states")
│async def benchmark_retrieval_txt(
│    dataset_item, valid_docs_per_parser, fixture_vector_cache, langfuse_trace
⋮

src\benchmark\benchmark_tools.py:
⋮
│class ToolParser(Protocol):
│    def invoke(self, args: dict[str, Any]) -> str: ...
│
⋮
│@fixture(scope="session")
│def docs_dict(fixture_parsed_cache: pd.DataFrame) -> dict[str, Any]:
⋮
│def skip_non_pdf(kwargs: dict[str, Any]) -> bool:
⋮
│def skip_non_docx(kwargs: dict[str, Any]) -> bool:
⋮
│def skip_non_txt(kwargs: dict[str, Any]) -> bool:
⋮
│async def _execute_tool_benchmark(
│    dataset_item: Any,
│    tool_name: str,
│    parser: ToolParser,
│    default_ext: str,
│    requires_pages: bool,
│    docs_dict: dict[str, Any],
│    langfuse_trace: Any,
⋮
│@benchmark(dataset_name="character_states", skip_if=skip_non_pdf)
│async def benchmark_tool_docling(
│    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
⋮
│@benchmark(dataset_name="character_states", skip_if=skip_non_pdf)
│async def benchmark_tool_pymupdf(
│    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
⋮
│@benchmark(dataset_name="character_states", skip_if=skip_non_docx)
│async def benchmark_tool_docx(
│    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
⋮
│@benchmark(dataset_name="character_states", skip_if=skip_non_txt)
│async def benchmark_tool_txt(
│    dataset_item: Any, docs_dict: dict[str, Any], langfuse_trace: Any
⋮

src\benchmark\confbenchmark.py:
⋮
│@fixture(scope="session")
│def fixture_parsed_cache(limit: int):
⋮
│@fixture(scope="session")
│def df_docs(fixture_parsed_cache):
⋮
│@fixture(scope="session")
│def fixture_vector_cache(fixture_parsed_cache):
⋮
│def _get_valid_document_ids_for_parser(parser_name: str) -> Optional[Set[str]]:
⋮
│@fixture(scope="session")
│def valid_docs_per_parser(fixture_vector_cache):
⋮
│@fixture(scope="session")
│async def fixture_synced_langfuse(skip_sync: bool, lf_client: Any, fixture_parsed_cache):
⋮

src\benchmark\config\__init__.py

src\benchmark\config\main.py:
⋮
│class BenchmarkSettings(BaseSettings):
⋮

src\benchmark\core\__init__.py

src\benchmark\core\decorators.py:
⋮
│def benchmark(
│    dataset_name: str = "default",
│    skip_if: Optional[Callable[[Any], bool]] = None,
│) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
│    """Flag an async function as a benchmark."""
│
│    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
│        if not hasattr(func, "__benchmark_metadata__"):
⋮
│        @functools.wraps(func)
│        def wrapper(*args: Any, **kwargs: Any) -> Any:
⋮
│def parametrize(
│    argnames: str, argvalues: List[Any]
│) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
│    """Parse string argnames and store them as metadata for execution expansion."""
│
│    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
│        if not hasattr(func, "__benchmark_metadata__"):
⋮
│        @functools.wraps(func)
│        def wrapper(*args: Any, **kwargs: Any) -> Any:
⋮
│def fixture(
│    scope: str = "function", name: Optional[str] = None
│) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
│    """Register a function (sync or async) as a dependency."""
│
│    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
│        fixture_name = name if name else func.__name__
⋮
│        @functools.wraps(func)
│        def wrapper(*args: Any, **kwargs: Any) -> Any:
⋮

src\benchmark\core\exceptions.py:
⋮
│class SkipBenchmark(Exception):
⋮
│class FailBenchmark(Exception):
⋮

src\benchmark\core\execution.py:
⋮
│def expand_permutations(
│    func: Callable[..., Any],
⋮
│async def execute_single_run(func: Callable[..., Any], kwargs: Dict[str, Any]) -> Any:
⋮

src\benchmark\core\fixtures.py:
⋮
│async def resolve_fixtures(
│    func: Callable[..., Any],
│    session_cache: Dict[str, Any],
│    extra_kwargs: Dict[str, Any] | None = None,
⋮

src\benchmark\core\registry.py:
⋮
│def add_benchmark(func: Callable[..., Any], metadata: Dict[str, Any]) -> None:
⋮
│def add_fixture(name: str, func: Callable[..., Any], scope: str) -> None:
⋮
│def get_benchmarks() -> List[Dict[str, Any]]:
⋮
│def get_fixtures() -> Dict[str, Dict[str, Any]]:
⋮

src\benchmark\core\runner.py:
⋮
│def discover_benchmarks(path: str, filters: list[str] = None) -> None:
⋮
│async def run_all(workers: int, limit: int, skip_sync: bool) -> None:
│    """
│    Execute all discovered benchmarks with the specified concurrency limit.
⋮
│    async def run_item(
│        func: Callable[..., Any],
│        kwargs: Dict[str, Any],
│        item_data: Any,
│        dataset_name: str,
│        dataset_item: Any,
│    ) -> None:
│        async with semaphore:
│            trace_name = f"{func.__name__}_{dataset_name}"
│
│            captured_output = {"value": None}
│
│            def langfuse_trace(output: Any = None) -> Any:
│                import langfuse as lf
│                client = lf.get_client()
│                if output is not None:
│                    captured_output["value"] = output
⋮
│                class DummyTrace:
│                    @property
│                    def id(self):
│                        try:
│                            return client.get_current_trace_id()
│                        except Exception:
⋮
│            @observe(name=trace_name)
│            async def _execute_traced_item():
⋮

src\benchmark\data\character_states.parquet

src\benchmark\data\documents.parquet

src\benchmark\modules\dataset\repositories\langfuse.py:
⋮
│@retry(
│    stop=stop_after_attempt(3),
│    wait=wait_exponential(multiplier=1, min=2, max=10),
│    reraise=True,
│)
│def _sync_create_dataset_item(client: Langfuse, dataset_name: str, item: Any) -> None:
⋮
│async def upsert_dataset_item(client: Langfuse, dataset_name: str, item: Any) -> None:
⋮

src\benchmark\modules\dataset\repositories\parquet.py:
⋮
│def read_documents(file_path: str) -> pd.DataFrame:
⋮
│def write_documents(df: pd.DataFrame, file_path: str) -> None:
⋮
│def read_character_states(file_path: str) -> pd.DataFrame:
⋮

src\benchmark\modules\dataset\services.py:
⋮
│def preparse_documents(
│    parquet_repo: Any, file_path: str, force: bool = False, limit: int | None = None
│) -> pd.DataFrame:
│    """Loads documents.parquet, iterates over rows, parses missing text using extractors, and saves
⋮
│    for idx, row in tqdm(
│        df_docs.iterrows(), total=len(df_docs), desc="Pre-parsing documents"
│    ):
│        document_id = row.get("id", row.get("document_id", f"idx_{idx}"))
⋮
│        def get_existing_page_content(parser_name: str, page_num: int) -> str | None:
⋮
│async def sync_datasets(
│    parquet_repo: Any, langfuse_repo: Any, client: Langfuse, df_docs: pd.DataFrame
⋮

src\benchmark\modules\evaluation\repositories\langfuse.py:
⋮
│def create_score_config(
│    client: Langfuse, name: str, categories: list[dict[str, Any]], description: str
⋮
│def create_evaluator(
│    client: Langfuse,
│    evaluator_name: str,
│    prompt_text: str,
│    score_config_id: str,
│    categories: list[str],
⋮
│def bind_evaluation_rule(
│    client: Langfuse, rule_name: str, evaluator_name: str, dataset_id: str
⋮

src\benchmark\modules\evaluation\services.py:
⋮
│def setup_evaluators(langfuse_repo: Any, client: Langfuse) -> None:
⋮

src\benchmark\modules\retrieval\services.py:
⋮
│def auto_ingest_vectors(df_docs: pd.DataFrame) -> None:
⋮

tests\integration\benchmark\test_benchmark_runner_integration.py:
⋮
│@benchmark(dataset_name="test_dataset")
│async def dummy_benchmark(dataset_item, item, langfuse_trace):
⋮
│@pytest.mark.asyncio
│async def test_run_all_integration():
│    # Setup our dummy benchmark in the registry
│    src.benchmark.core.registry._BENCHMARKS = [
│        {"func": dummy_benchmark, "metadata": {"dataset_name": "test_dataset"}}
⋮
│    def mock_send(request, *args, **kwargs):
⋮
│    with patch.dict(os.environ, {
│        "LANGFUSE_PUBLIC_KEY": "pk-lf-123",
│        "LANGFUSE_SECRET_KEY": "sk-lf-123",
│        "LANGFUSE_HOST": "https://dummy.langfuse.com"
│    }):
│        with patch("httpx.Client.send", side_effect=mock_send) as mock_send_call:
│            with patch("src.benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as moc
│                
│                # Mock langfuse client
│                mock_lf_client = MagicMock()
│                mock_lf_client.get_current_trace_id.return_value = "trace_123"
│                
│                with patch("langfuse.get_client", return_value=mock_lf_client):
│                    # provide trace closure and item
│                    async def resolve_side_effect(func, session_cache, extra_kwargs):
│                        if func == benchmark_setup:
│                            return {}
│                        return {
│                            "dataset_item": extra_kwargs["dataset_item"],
│                            "item": extra_kwargs["item"],
│                            "langfuse_trace": extra_kwargs["langfuse_trace"]
⋮
│@pytest.mark.asyncio
│async def test_parquet_clone_generation():
⋮

tests\unit\benchmark\core\test_decorators.py:
⋮
│@patch("src.benchmark.core.decorators.add_benchmark")
│def test_benchmark_decorator(mock_add_benchmark):
│    @benchmark(dataset_name="test_dataset")
│    def sample_func():
⋮
│def test_parametrize_decorator():
│    @parametrize("arg1", [1, 2])
│    @parametrize("arg2,arg3", [(3, 4)])
│    def sample_func():
⋮
│@patch("src.benchmark.core.decorators.add_fixture")
│def test_fixture_decorator(mock_add_fixture):
│    @fixture(scope="session", name="custom_name")
│    def sample_fixture():
⋮
│@patch("src.benchmark.core.decorators.add_fixture")
│def test_fixture_decorator_default_name(mock_add_fixture):
│    @fixture(scope="function")
│    def default_name_fixture():
⋮

tests\unit\benchmark\core\test_execution.py:
⋮
│def test_expand_permutations_no_metadata():
│    def func():
⋮
│def test_expand_permutations_multiple():
│    @parametrize("b", [3, 4])
│    @parametrize("a", [1, 2])
│    def func():
⋮
│@pytest.mark.asyncio
│async def test_execute_single_run_sync():
│    def sync_func(x):
⋮
│@pytest.mark.asyncio
│async def test_execute_single_run_async():
│    async def async_func(x):
⋮
│@pytest.mark.asyncio
│async def test_execute_single_run_skip_fail(caplog):
│    caplog.set_level("DEBUG")
│    def skip_func():
⋮
│    def fail_func():
⋮

tests\unit\benchmark\core\test_fixtures.py:
⋮
│@pytest.fixture
│def mock_get_fixtures():
⋮
│@pytest.mark.asyncio
│async def test_resolve_fixtures_basic(mock_get_fixtures):
│    def fix1():
⋮
│    async def fix2(fix1):
⋮
│    async def target(fix2, extra_arg):
⋮
│@pytest.mark.asyncio
│async def test_resolve_fixtures_session_cache(mock_get_fixtures):
│    call_count = 0
│    def session_fix():
⋮
│    def target1(session_fix):
⋮
│    def target2(session_fix):
⋮

tests\unit\benchmark\core\test_runner.py:
⋮
│def test_discover_benchmarks(tmp_path):
⋮
│@pytest.mark.asyncio
⋮
│async def test_run_all(mock_get_benchmarks, mock_langfuse):
│    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
⋮
│    async def sample_bench(**kwargs):
⋮
│@pytest.mark.asyncio
⋮
│async def test_run_all_skip_fail_handled(mock_get_benchmarks, mock_langfuse):
│    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
⋮
│    async def failing_bench(**kwargs):
⋮
│@pytest.mark.asyncio
⋮
│async def test_run_all_skip_if(mock_get_benchmarks, mock_langfuse):
│    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
⋮
│    async def sample_bench(**kwargs):
⋮
│    def skip_condition(kwargs):
⋮
│@pytest.mark.asyncio
⋮
│async def test_run_all_dataset_run_item_creation(mock_get_benchmarks, mock_langfuse):
│    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
⋮
│    async def successful_bench(langfuse_trace, **kwargs):
⋮
│    with patch("langfuse.get_client", return_value=mock_lf):
│        mock_lf.get_current_trace_id.return_value = "trace_abc"
│        with patch("src.benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as mock_re
│            # Provide the langfuse_trace closure that's injected by run_all
│            async def resolve_side_effect(func, session_cache, extra_kwargs):
│                if func.__name__ == "benchmark_setup":
│                    return {}
⋮

tests\unit\benchmark\test_benchmark_tools.py:
⋮
│class MockDatasetItem:
│    def __init__(self, input_data):
⋮
│def test_skip_conditions():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_success():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_missing_text():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_missing_page():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_success_with_list():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_missing_text_empty_list():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_nan_handling():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_handles_numpy_pages():
⋮
│@pytest.mark.asyncio
│async def test_execute_tool_benchmark_doc_not_found():
⋮

tests\unit\scripts\test_parse_documents.py:
⋮
│@pytest.fixture
│def mock_args():
⋮
│@pytest.fixture
│def sample_df():
⋮
│@patch("scripts.parse_documents.pd.read_parquet")
⋮
│def test_parse_documents_success(
│    mock_txt,
│    mock_docling,
│    mock_pymupdf,
│    mock_fitz_open,
│    mock_to_parquet,
│    mock_read_parquet,
│    sample_df,
│    mock_args,
⋮
│@patch("scripts.parse_documents.pd.read_parquet")
⋮
│def test_parse_documents_error_boundary(
│    mock_docling,
│    mock_pymupdf,
│    mock_fitz_open,
│    mock_to_parquet,
│    mock_read_parquet,
│    mock_args,
│):
│    df = pd.DataFrame(
│        {
│            "document_id": ["doc1"],
│            "mime_type": ["application/pdf"],
│            "filename": ["test1.pdf"],
│            "file_bytes": [b"pdf content"],
│        }
⋮
│    def pymupdf_side_effect(args_dict, *args, **kwargs):
⋮

```