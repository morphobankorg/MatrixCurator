import sys
from unittest.mock import MagicMock
sys.modules["sqlite_vec"] = MagicMock()

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from matrixcurator_benchmark.retrieval import run_retrieval_benchmarks, PARSERS

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.retrieval.run_dataset_benchmark", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.retrieval._get_valid_document_ids_for_parser")
async def test_run_retrieval_benchmarks_targets_relevant_and_full_page(mock_get_valid, mock_run_benchmark):
    mock_get_valid.return_value = {"doc_1"}
    
    docs_dict = {}
    await run_retrieval_benchmarks(limit=1, workers=1, docs_dict=docs_dict)
    
    # Should be called 4 times for the 4 PARSERS
    assert mock_run_benchmark.call_count == 4
    
    run_names = [call[1]["run_name"] for call in mock_run_benchmark.call_args_list]
    assert "benchmark_retrieval_docling_full_page" in run_names
    assert "benchmark_retrieval_docling_relevant" in run_names
    
    # Check that retrieve_context gets correct args in task_fn
    task_fn_full_page = [call[1]["task_fn"] for call in mock_run_benchmark.call_args_list if call[1]["run_name"] == "benchmark_retrieval_docling_full_page"][0]
    
    with patch("matrixcurator_benchmark.retrieval.retrieve_context", new_callable=AsyncMock) as mock_retrieve:
        mock_item = MagicMock()
        mock_item.input = {"document_id": "doc_1"}
        await task_fn_full_page(item=mock_item)
        
        mock_retrieve.assert_called_once_with(
            query="Character 1", 
            document_id="doc_1", 
            parser_name="docling",
            full_page_retrieval=True
        )
