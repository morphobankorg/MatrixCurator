import logging
from functools import wraps
import sentry_sdk

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 1. Execution logging decorator
def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Function '{func.__name__}' started")
        result = func(*args, **kwargs)
        logger.info(f"Function '{func.__name__}' completed")
        return result
    return wrapper

# 2. Sentry exception handler decorator
def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if sentry_sdk:
                # Capture exception to Sentry
                sentry_sdk.capture_exception(e)
                
                # Add custom context to the event
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("function_args", {
                        "positional": args,
                        "keyword": kwargs
                    })
                    scope.set_tag("function_name", func.__name__)

            # Log locally as well
            logger.error(f"Exception in '{func.__name__}': {str(e)}")
            
            # Re-raise the original exception
            raise
    return wrapper