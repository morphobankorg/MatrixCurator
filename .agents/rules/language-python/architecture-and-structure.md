---
description: Architectural patterns, DDD, CQRS, and project structure
globs: *.py
---
# Architecture and Structure Standards

## 🎯 Directives
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

## 📝 Examples

### ✅ DO
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

### ❌ DON'T
```python
@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    session = get_session()
    batches = session.query(Batch).all()
    line = OrderLine(request.json['orderid'], request.json['sku'], request.json['qty'])
    model.allocate(line, batches)
    session.commit()
    return jsonify({'status': 'ok'})