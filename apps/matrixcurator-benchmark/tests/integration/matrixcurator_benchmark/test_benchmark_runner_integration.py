import pytest
import asyncio
import json
import os
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock

import httpx

from matrixcurator_benchmark.core.runner import run_all
from matrixcurator_benchmark.core.decorators import benchmark
import matrixcurator_benchmark.core.registry
from matrixcurator_benchmark.confbenchmark import fixture_parsed_cache as benchmark_setup

# Dummy benchmark to test orchestration
@benchmark(dataset_name="test_dataset")
async def dummy_benchmark(dataset_item, item, langfuse_trace):
    langfuse_trace("dummy_output")

@pytest.mark.asyncio
async def test_run_all_integration():
    # Setup our dummy benchmark in the registry
    matrixcurator_benchmark.core.registry._BENCHMARKS = [
        {"func": dummy_benchmark, "metadata": {"dataset_name": "test_dataset"}}
    ]

    mock_dataset_response = {
        "id": "ds_123",
        "name": "test_dataset",
        "description": "test",
        "metadata": {},
        "projectId": "proj_123",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }

    mock_dataset_items_response = {
        "data": [
            {
                "id": "item_123",
                "input": {"val": 1},
                "expectedOutput": {"val": 1},
                "datasetId": "ds_123",
                "datasetName": "test_dataset",
                "status": "ACTIVE",
                "metadata": {},
                "mediaReferences": [],
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z"
            }
        ],
        "meta": {"page": 1, "limit": 50, "totalPages": 1, "totalItems": 1}
    }
    
    mock_run_item_response = {
        "id": "run_item_123",
        "datasetItemId": "item_123",
        "datasetRunId": "run_123",
        "traceId": "trace_123",
        "observationId": None,
        "projectId": "proj_123",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }
    
    def mock_send(request, *args, **kwargs):
        url = str(request.url)
        print(f"Intercepted request: {request.method} {url}")
        
        # We need to distinguish between /datasets/test_dataset and /dataset-items?datasetName=test_dataset
        if "/datasets/test_dataset" in url:
            if request.method == "GET":
                return httpx.Response(200, json=mock_dataset_response, request=request)
        elif "/dataset-items" in url:
            if request.method == "GET":
                return httpx.Response(200, json=mock_dataset_items_response, request=request)
        elif "/dataset-run-items" in url:
            if request.method == "POST":
                return httpx.Response(200, json=mock_run_item_response, request=request)
        
        # Default response for trace uploads / batch / anything else
        return httpx.Response(200, json={}, request=request)
    
    # We patch httpx.Client.send which is the core method for synchronous HTTPX clients
    # used by langfuse for API calls.
    with patch.dict(os.environ, {
        "LANGFUSE_PUBLIC_KEY": "pk-lf-123",
        "LANGFUSE_SECRET_KEY": "sk-lf-123",
        "LANGFUSE_HOST": "https://dummy.langfuse.com"
    }):
        with patch("httpx.Client.send", side_effect=mock_send) as mock_send_call:
            with patch("matrixcurator_benchmark.core.runner.resolve_fixtures", new_callable=AsyncMock) as mock_resolve:
                
                # Mock langfuse client
                mock_lf_client = MagicMock()
                mock_lf_client.get_current_trace_id.return_value = "trace_123"
                
                with patch("langfuse.get_client", return_value=mock_lf_client):
                    # provide trace closure and item
                    async def resolve_side_effect(func, session_cache, extra_kwargs):
                        if func.__name__ == "benchmark_setup" or func.__name__ == "fixture_parsed_cache":
                            return {}
                        return {
                            "dataset_item": extra_kwargs["dataset_item"],
                            "item": extra_kwargs["item"],
                            "langfuse_trace": extra_kwargs["langfuse_trace"]
                        }
                    mock_resolve.side_effect = resolve_side_effect
                    
                    with patch("lume.integrations.langfuse.langfuse.Langfuse.flush") as mock_flush:
                        await run_all(workers=1, limit=1, skip_sync=True)
                    
                        # End-to-End Orchestration: Check if set_current_trace_io was called
                        mock_lf_client.set_current_trace_io.assert_called_once_with(output="dummy_output")
                        
                        # Trace Flush Verification
                        mock_flush.assert_called()
                
    # Verify that dataset run item was created via API call
    dataset_run_item_calls = [
        call for call in mock_send_call.call_args_list 
        if "/api/public/dataset-run-items" in str(call[0][0].url) and call[0][0].method == "POST"
    ]
    
    assert len(dataset_run_item_calls) == 1
    
    # Verify the body of the POST request
    request = dataset_run_item_calls[0][0][0]
    body = json.loads(request.read().decode("utf-8"))
    
    assert body["datasetItemId"] == "item_123"
    assert body["runName"] == "dummy_benchmark_test_dataset"
    assert "traceId" in body


@pytest.mark.asyncio
async def test_parquet_clone_generation():
    # Mocking os.path.exists and pd.read_parquet
    mock_df = pd.DataFrame([
        {
            "id": "doc1",
            "mime_type": "text/plain",
            "filename": "test.txt",
            "file_bytes": b"fake content",
            "text": None
        }
    ])

    with patch("matrixcurator_benchmark.modules.dataset.services.os.path.exists", return_value=True):
        with patch("matrixcurator_benchmark.modules.dataset.services.os.makedirs"):
            with patch("pyarrow.parquet.read_table") as mock_read_table:
                mock_table = MagicMock()
                mock_table.to_pylist.return_value = mock_df.to_dict('records')
                mock_read_table.return_value = mock_table
                
                with patch("matrixcurator_benchmark.modules.dataset.repositories.parquet.write_documents") as mock_write_docs:
                    mock_tool = MagicMock()
                    mock_tool.ainvoke = AsyncMock(return_value="Parsed TXT text")
                    with patch("matrixcurator_benchmark.modules.dataset.services.parse_with_txt", mock_tool):
                        # We are testing fixture_parsed_cache
                        await benchmark_setup(limit=1)
                        
                        # Verify write_documents is called
                        mock_write_docs.assert_called()
                        
                        # Verify that text column was populated with JSON array
                        saved_docs = mock_write_docs.call_args[0][0]
                        
                        text_json = saved_docs[0]["text"]
                        assert text_json is not None
                        
                        assert isinstance(text_json, list)
                        assert len(text_json) == 1
                        assert text_json[0]["parser"] == "txt"
                        assert text_json[0]["pages"][0]["content"] == "Parsed TXT text"


