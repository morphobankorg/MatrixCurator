import pytest
from unittest.mock import patch, MagicMock
from matrixcurator_benchmark.services import run_dataset_benchmark

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
@patch("matrixcurator_benchmark.services.asyncio.to_thread")
async def test_run_dataset_benchmark_success(mock_to_thread, mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    # Mock items
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    
    item2 = MagicMock()
    item2.input = {"document_id": "doc2"}
    
    mock_dataset.items = [item1, item2]
    
    mock_task_fn = MagicMock()
    
    await run_dataset_benchmark("test_dataset", "test_run", mock_task_fn, limit=0, workers=2)
    
    # Check that to_thread was called with run_experiment
    mock_to_thread.assert_called_once()
    args, kwargs = mock_to_thread.call_args
    assert args[0] == mock_lf.run_experiment
    assert kwargs["name"] == "test_run"
    assert kwargs["data"] == [item1, item2]
    assert kwargs["task"] == mock_task_fn
    assert kwargs["evaluators"] == []
    assert kwargs["max_concurrency"] == 2


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
@patch("matrixcurator_benchmark.services.asyncio.to_thread")
async def test_run_dataset_benchmark_limit(mock_to_thread, mock_langfuse_class):
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
    
    mock_task_fn = MagicMock()
    
    # Limit to 1 document
    await run_dataset_benchmark("test_dataset", "test_run", mock_task_fn, limit=1, workers=2)
    
    mock_to_thread.assert_called_once()
    _, kwargs = mock_to_thread.call_args
    assert len(kwargs["data"]) == 2
    assert kwargs["data"] == [item1, item2]


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
@patch("matrixcurator_benchmark.services.asyncio.to_thread")
async def test_run_dataset_benchmark_filter(mock_to_thread, mock_langfuse_class):
    mock_lf = MagicMock()
    mock_langfuse_class.return_value = mock_lf
    mock_dataset = MagicMock()
    mock_lf.get_dataset.return_value = mock_dataset
    
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    item2 = MagicMock()
    item2.input = {"document_id": "doc2"}
    
    mock_dataset.items = [item1, item2]
    
    mock_task_fn = MagicMock()
    
    def mock_filter(item):
        return item.input.get("document_id") == "doc2"
    
    await run_dataset_benchmark(
        "test_dataset", "test_run", mock_task_fn, limit=0, workers=2, filter_fn=mock_filter
    )
    
    mock_to_thread.assert_called_once()
    _, kwargs = mock_to_thread.call_args
    assert len(kwargs["data"]) == 1
    assert kwargs["data"] == [item2]


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.services.langfuse.Langfuse")
@patch("matrixcurator_benchmark.services.asyncio.to_thread")
async def test_run_dataset_benchmark_resilient_input_parsing(mock_to_thread, mock_langfuse_class):
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
    
    mock_task_fn = MagicMock()
    
    await run_dataset_benchmark("test_dataset", "test_run", mock_task_fn, limit=2, workers=1)
    
    mock_to_thread.assert_called_once()
    _, kwargs = mock_to_thread.call_args
    assert len(kwargs["data"]) == 2
    assert kwargs["data"] == [item1, item2]
