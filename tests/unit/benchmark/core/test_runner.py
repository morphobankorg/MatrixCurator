import pytest
from unittest.mock import patch, MagicMock, AsyncMock, create_autospec
from pathlib import Path

from src.benchmark.core.runner import discover_benchmarks, run_all
from src.benchmark.core.exceptions import SkipBenchmark
import langfuse
import langfuse.api.client

def test_discover_benchmarks(tmp_path):
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir()
    bench_file = bench_dir / "benchmark_dummy.py"
    bench_file.write_text("def dummy(): pass")
    
    with patch("src.benchmark.core.runner.importlib.import_module") as mock_import:
        discover_benchmarks(str(bench_dir))
        mock_import.assert_called_once_with("benchmarks.benchmark_dummy")

@pytest.mark.asyncio
@patch("src.benchmark.core.runner.langfuse")
@patch("src.benchmark.core.runner.get_benchmarks")
async def test_run_all(mock_get_benchmarks, mock_langfuse):
    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
    mock_api = create_autospec(langfuse.api.client.LangfuseAPI, instance=True)
    mock_lf.api = mock_api
    if hasattr(mock_langfuse, "Langfuse"):
        mock_langfuse.Langfuse.return_value = mock_lf
    else:
        mock_langfuse = mock_lf
        
    mock_dataset = MagicMock()
    mock_item = MagicMock()
    mock_item.input = {"val": 1}
    mock_item.id = "item_123"
    mock_dataset.items = [mock_item]
    mock_lf.get_dataset.return_value = mock_dataset
    
    call_count = 0
    async def sample_bench(**kwargs):
        nonlocal call_count
        call_count += 1
        
    mock_get_benchmarks.return_value = [
        {"func": sample_bench, "metadata": {"dataset_name": "test_ds"}}
    ]
    
    with patch("src.benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = {"item": mock_item.input, "dataset_item": mock_item }
        await run_all(workers=1, limit=1, skip_sync=True)
        
    assert call_count == 1

@pytest.mark.asyncio
@patch("src.benchmark.core.runner.langfuse")
@patch("src.benchmark.core.runner.get_benchmarks")
async def test_run_all_skip_fail_handled(mock_get_benchmarks, mock_langfuse):
    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
    mock_api = create_autospec(langfuse.api.client.LangfuseAPI, instance=True)
    mock_lf.api = mock_api
    if hasattr(mock_langfuse, "Langfuse"):
        mock_langfuse.Langfuse.return_value = mock_lf
    else:
        mock_langfuse = mock_lf
        
    mock_dataset = MagicMock()
    mock_item = MagicMock()
    mock_item.id = "item_123"
    mock_dataset.items = [mock_item]
    mock_lf.get_dataset.return_value = mock_dataset
    
    async def failing_bench(**kwargs):
        raise SkipBenchmark("Skip me")
        
    mock_get_benchmarks.return_value = [
        {"func": failing_bench, "metadata": {"dataset_name": "test_ds"}}
    ]
    
    with patch("src.benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = {}
        await run_all(workers=1, limit=1, skip_sync=True)

@pytest.mark.asyncio
@patch("src.benchmark.core.runner.langfuse")
@patch("src.benchmark.core.runner.get_benchmarks")
async def test_run_all_skip_if(mock_get_benchmarks, mock_langfuse):
    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
    mock_api = create_autospec(langfuse.api.client.LangfuseAPI, instance=True)
    mock_lf.api = mock_api
    if hasattr(mock_langfuse, "Langfuse"):
        mock_langfuse.Langfuse.return_value = mock_lf
    else:
        mock_langfuse = mock_lf
        
    mock_dataset = MagicMock()
    mock_item = MagicMock()
    mock_item.input = {"val": 1}
    mock_item.id = "item_123"
    mock_dataset.items = [mock_item]
    mock_lf.get_dataset.return_value = mock_dataset
    
    call_count = 0
    async def sample_bench(**kwargs):
        nonlocal call_count
        call_count += 1
        
    def skip_condition(kwargs):
        return kwargs.get("item", {}).get("val") == 1

    sample_bench.__benchmark_metadata__ = {"dataset_name": "test_ds", "skip_if": skip_condition}
        
    mock_get_benchmarks.return_value = [
        {"func": sample_bench, "metadata": {"dataset_name": "test_ds", "skip_if": skip_condition}}
    ]
    
    with patch("src.benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = {"item": mock_item.input, "dataset_item": mock_item}
        await run_all(workers=1, limit=1, skip_sync=True)
        
    # The benchmark function should not be executed because skip_if returns True
    assert call_count == 0
    # Langfuse span update should not be called
    mock_lf.set_current_trace_io.assert_not_called()

@pytest.mark.asyncio
@patch("src.benchmark.core.runner.langfuse")
@patch("src.benchmark.core.runner.get_benchmarks")
async def test_run_all_dataset_run_item_creation(mock_get_benchmarks, mock_langfuse):
    mock_lf = create_autospec(langfuse.Langfuse, instance=True)
    mock_api = create_autospec(langfuse.api.client.LangfuseAPI, instance=True)
    mock_lf.api = mock_api
    if hasattr(mock_langfuse, "Langfuse"):
        mock_langfuse.Langfuse.return_value = mock_lf
    else:
        mock_langfuse = mock_lf
        
    mock_dataset = MagicMock()
    mock_item = MagicMock()
    mock_item.id = "item_123"
    mock_dataset.items = [mock_item]
    mock_lf.get_dataset.return_value = mock_dataset
    
    async def successful_bench(langfuse_trace, **kwargs):
        langfuse_trace("test output")
        
    mock_get_benchmarks.return_value = [
        {"func": successful_bench, "metadata": {"dataset_name": "test_ds"}}
    ]
    
    with patch("langfuse.get_client", return_value=mock_lf):
        mock_lf.get_current_trace_id.return_value = "trace_abc"
        with patch("src.benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as mock_resolve:
            # Provide the langfuse_trace closure that's injected by run_all
            async def resolve_side_effect(func, session_cache, extra_kwargs):
                if func.__name__ == "benchmark_setup":
                    return {}
                return {"langfuse_trace": extra_kwargs["langfuse_trace"]}
            mock_resolve.side_effect = resolve_side_effect
            await run_all(workers=1, limit=1, skip_sync=True)

        mock_lf.api.dataset_run_items.create.assert_called_once_with(
            run_name="successful_bench_test_ds",
            dataset_item_id="item_123",
            trace_id="trace_abc"
        )


