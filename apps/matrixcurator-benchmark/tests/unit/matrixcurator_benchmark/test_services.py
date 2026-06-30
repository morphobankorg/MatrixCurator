import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from matrixcurator_benchmark.services import run_dataset_benchmark
from matrixcurator_benchmark.exceptions import SkipBenchmark, FailBenchmark


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
async def test_run_dataset_benchmark_success(mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    # Mock items
    item1 = MagicMock()
    item1.id = "item1_id"
    item1.input = {"document_id": "doc1"}
    
    item2 = MagicMock()
    item2.id = "item2_id"
    item2.input = {"document_id": "doc2"}
    
    mock_dataset.items = [item1, item2]
    
    # Mock trace
    mock_trace = MagicMock()
    mock_trace.id = "trace_id_123"
    mock_trace.trace_id = "trace_id_123_456"
    mock_lf.start_as_current_observation.return_value.__enter__.return_value = mock_trace
    
    mock_process_fn = AsyncMock()
    
    await run_dataset_benchmark("test_dataset", "test_run", mock_process_fn, limit=0, workers=2)
    
    # Check that process_fn was called for each item
    assert mock_process_fn.call_count == 2
    mock_process_fn.assert_any_call(item1, mock_trace)
    mock_process_fn.assert_any_call(item2, mock_trace)
    
    # Check that link was called
    assert mock_lf.api.dataset_run_items.create.call_count == 2


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
async def test_run_dataset_benchmark_limit(mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    
    item2 = MagicMock()
    item2.input = {"document_id": "doc1"} # Same doc id
    
    item3 = MagicMock()
    item3.input = {"document_id": "doc2"}
    
    mock_dataset.items = [item1, item2, item3]
    
    mock_process_fn = AsyncMock()
    
    # Limit to 1 document
    await run_dataset_benchmark("test_dataset", "test_run", mock_process_fn, limit=1, workers=2)
    
    # Should only process item1 and item2 because they are the first document
    assert mock_process_fn.call_count == 2
    

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
async def test_run_dataset_benchmark_skip(mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    mock_dataset.items = [item1]
    
    mock_trace = MagicMock()
    mock_lf.start_as_current_observation.return_value.__enter__.return_value = mock_trace
    
    async def mock_process_fn(item, trace):
        raise SkipBenchmark("skip")
    
    await run_dataset_benchmark("test_dataset", "test_run", mock_process_fn, limit=0, workers=2)
    
    # Link should NOT be called
    assert mock_lf.api.dataset_run_items.create.call_count == 0


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
async def test_run_dataset_benchmark_fail(mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    mock_dataset.items = [item1]
    
    mock_trace = MagicMock()
    mock_lf.start_as_current_observation.return_value.__enter__.return_value = mock_trace
    
    async def mock_process_fn(item, trace):
        raise FailBenchmark("fail")
    
    await run_dataset_benchmark("test_dataset", "test_run", mock_process_fn, limit=0, workers=2)
    
    # Trace should be updated with error
    mock_trace.update.assert_called_with(level="ERROR", status_message="fail")
    
    # Link SHOULD be called
    assert mock_lf.api.dataset_run_items.create.call_count == 1


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
async def test_run_dataset_benchmark_resilient_input_parsing(mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    # 1. Dict input
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    
    # 2. Object input
    class ObjInput:
        document_id = "doc2"
    item2 = MagicMock()
    item2.input = ObjInput()
    
    # 3. JSON string input
    item3 = MagicMock()
    item3.input = '{"document_id": "doc3"}'
    
    mock_dataset.items = [item1, item2, item3]
    
    mock_process_fn = AsyncMock()
    
    await run_dataset_benchmark("test_dataset", "test_run", mock_process_fn, limit=3, workers=1)
    
    assert mock_process_fn.call_count == 3
