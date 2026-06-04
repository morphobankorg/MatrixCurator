import logging
import os
import sys
from typing import Any, Dict

import structlog
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from matrixcurator.config.main import settings
from matrixcurator.integrations.sentry import init_sentry
from matrixcurator.integrations.posthog import init_posthog

def _extract_and_store_windmill_trace_context() -> None:
    """Extracts trace_id and span_id from TRACEPARENT and stores in settings."""
    traceparent = os.getenv("TRACEPARENT")
    if traceparent:
        parts = traceparent.split("-")
        if len(parts) >= 3:
            settings.trace_id = parts[1]
            settings.span_id = parts[2]

def add_otel_context(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Injects OpenTelemetry trace_id and span_id into the log record."""
    # 1. Try to get it from the active OTel span
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    else:
        # 2. Fallback to the context stored in settings (from Windmill)
        if settings.trace_id:
            event_dict["trace_id"] = settings.trace_id
        if settings.span_id:
            event_dict["span_id"] = settings.span_id
            
    return event_dict

def _setup_otel_logger_provider() -> LoggerProvider:
    """Initializes the OpenTelemetry LoggerProvider with an OTLP exporter."""
    logger_provider = LoggerProvider()
    
    # Only add the exporter if an endpoint is configured
    if settings.otel_exporter_otlp_endpoint or settings.otel_exporter_otlp_logs_endpoint:
        try:
            exporter = OTLPLogExporter()
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        except Exception:
            # Silent failure for OTLP exporter if network is unreachable
            pass
    
    set_logger_provider(logger_provider)
    return logger_provider

# Export get_logger for use throughout the application
get_logger = structlog.get_logger

def setup_logging(app_name: str, log_level: int = logging.INFO) -> None:
    """
    Configures structlog, routes standard logging through it, 
    and initializes Sentry and PostHog telemetry.
    """
    # 1. Initialize Telemetry (Sentry & PostHog)
    init_sentry(app_name)
    init_posthog(app_name)

    # 2. Extract Windmill context before configuring loggers
    _extract_and_store_windmill_trace_context()

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_otel_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 3. Console Handler (Human-readable)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=shared_processors,
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # 4. OTLP Handler (Structured JSON/Protobuf)
    logger_provider = _setup_otel_logger_provider()
    otlp_handler = LoggingHandler(level=log_level, logger_provider=logger_provider)

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate logs and override FastAPI/Uvicorn logs
    root_logger.handlers.clear()
    
    root_logger.addHandler(console_handler)
    
    # Only add OTLP handler if endpoint is configured to avoid connection errors
    if settings.otel_exporter_otlp_endpoint or settings.otel_exporter_otlp_logs_endpoint:
        root_logger.addHandler(otlp_handler)
        
    root_logger.setLevel(log_level)
