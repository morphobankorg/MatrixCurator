import pytest
import os
from unittest.mock import patch, MagicMock
from matrixcurator.config.logging import (
    _extract_and_store_windmill_trace_context,
    add_otel_context,
    _setup_otel_logger_provider
)
from matrixcurator.config.main import settings

@patch.dict(os.environ, {"TRACEPARENT": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"})
def test_extract_windmill_context_from_traceparent():
    """Test Case: Extract Windmill Context from TRACEPARENT"""
    _extract_and_store_windmill_trace_context()
    
    assert settings.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert settings.span_id == "00f067aa0ba902b7"

@patch("matrixcurator.config.logging.trace.get_current_span")
def test_inject_context_fallback_to_settings(mock_get_current_span):
    """Test Case: Inject Context into Log Event (Fallback to Settings)"""
    mock_get_current_span.return_value = None
    settings.trace_id = "test_trace_123"
    settings.span_id = "test_span_456"
    
    event_dict = {"event": "test"}
    result = add_otel_context(None, "info", event_dict)
    
    assert result["trace_id"] == "test_trace_123"
    assert result["span_id"] == "test_span_456"

@patch("matrixcurator.config.logging.trace.get_current_span")
def test_inject_context_active_otel_span(mock_get_current_span):
    """Test Case: Inject Context into Log Event (Active OTel Span)"""
    mock_span = MagicMock()
    mock_span.get_span_context.return_value.is_valid = True
    mock_span.get_span_context.return_value.trace_id = 0x12345
    mock_span.get_span_context.return_value.span_id = 0x67890
    mock_get_current_span.return_value = mock_span
    
    event_dict = {"event": "test"}
    result = add_otel_context(None, "info", event_dict)
    
    assert result["trace_id"] == format(0x12345, "032x")
    assert result["span_id"] == format(0x67890, "016x")

@patch("matrixcurator.config.logging.settings")
@patch("matrixcurator.config.logging.OTLPLogExporter")
def test_otlp_exporter_network_failure(mock_otlp_exporter, mock_settings):
    """Test Case: OTLP Exporter Network Failure During Initialization"""
    mock_settings.otel_exporter_otlp_endpoint = "http://invalid-endpoint:4318"
    mock_otlp_exporter.side_effect = Exception("ConnectionError")
    
    # Should not raise an exception
    provider = _setup_otel_logger_provider()
    
    assert provider is not None
