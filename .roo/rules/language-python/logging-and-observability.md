---
description: Logging practices, tracebacks, and system observability
globs: *.py
---
# Logging and Observability Standards

## 🎯 Directives
- ALWAYS use the standard `logging` module. NEVER use `print()` for application logs in production code.
- ALWAYS use `logging.exception("message")` inside `except` blocks to automatically log the full stack trace of the caught exception.
- ALWAYS configure a `StreamHandler` outputting to the console (stdout/stderr) in containerized environments (Docker) so logs are captured by the container runtime.
- ALWAYS inject debug log statements immediately before invoking handlers in a Message Bus or Event-Driven Architecture (e.g., `logger.debug('handling event %s', event)`).
- ALWAYS use structured logging or include contextual identifiers (e.g., `order_id`, `user_id`) in log messages to facilitate tracing across distributed systems.
- ALWAYS configure appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Use `INFO` for normal operational milestones and `DEBUG` for detailed tracing.
- ALWAYS capture warnings in the logging system using `logging.captureWarnings(True)` in production configurations.

## 📝 Examples

### ✅ DO
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

### ❌ DON'T
```python
def process_payment(order_id: str, amount: float) -> None:
    print(f"Processing payment for {order_id}")
    try:
        charge_card(amount)
    except PaymentGatewayError as e:
        print(f"Error: {e}") # Loses the stack trace