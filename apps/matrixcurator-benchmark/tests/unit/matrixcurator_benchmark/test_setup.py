import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from matrixcurator_benchmark.setup import bootstrap_environment


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.setup.retrieval_services.auto_ingest_vectors")
@patch("matrixcurator_benchmark.setup.evaluation_services.setup_evaluators")
@patch("matrixcurator_benchmark.setup.dataset_services.sync_datasets", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.setup.dataset_services.preparse_documents", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.setup.langfuse.Langfuse")
async def test_bootstrap_environment_full(
    mock_langfuse,
    mock_preparse,
    mock_sync,
    mock_setup_evaluators,
    mock_auto_ingest
):
    mock_preparse.return_value = [{"document_id": "doc_1"}, {"id": "doc_2"}]
    
    docs_dict = await bootstrap_environment(limit=10, skip_sync=False, no_cache=False, targets=["agents"])
    
    mock_preparse.assert_called_once()
    mock_sync.assert_called_once()
    mock_setup_evaluators.assert_called_once()
    mock_auto_ingest.assert_called_once()
    
    assert docs_dict == {"doc_1": {"document_id": "doc_1"}, "doc_2": {"id": "doc_2"}}


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.setup.retrieval_services.auto_ingest_vectors")
@patch("matrixcurator_benchmark.setup.evaluation_services.setup_evaluators")
@patch("matrixcurator_benchmark.setup.dataset_services.sync_datasets", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.setup.dataset_services.preparse_documents", new_callable=AsyncMock)
async def test_bootstrap_environment_skip_sync(
    mock_preparse,
    mock_sync,
    mock_setup_evaluators,
    mock_auto_ingest
):
    mock_preparse.return_value = [{"document_id": "doc_1"}]
    
    docs_dict = await bootstrap_environment(limit=10, skip_sync=True, no_cache=False, targets=["agents"])
    
    mock_preparse.assert_called_once()
    mock_sync.assert_not_called()
    mock_setup_evaluators.assert_not_called()
    mock_auto_ingest.assert_called_once()
    
    assert "doc_1" in docs_dict


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.setup.retrieval_services.auto_ingest_vectors")
@patch("matrixcurator_benchmark.setup.evaluation_services.setup_evaluators")
@patch("matrixcurator_benchmark.setup.dataset_services.sync_datasets", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.setup.dataset_services.preparse_documents", new_callable=AsyncMock)
async def test_bootstrap_environment_tools_target(
    mock_preparse,
    mock_sync,
    mock_setup_evaluators,
    mock_auto_ingest
):
    mock_preparse.return_value = [{"document_id": "doc_1"}]
    
    docs_dict = await bootstrap_environment(limit=10, skip_sync=False, no_cache=False, targets=["tools"])
    
    mock_preparse.assert_called_once()
    mock_sync.assert_called_once()
    mock_setup_evaluators.assert_called_once()
    mock_auto_ingest.assert_not_called()
    
    assert "doc_1" in docs_dict


@pytest.mark.asyncio
@patch("matrixcurator_benchmark.setup.retrieval_services.auto_ingest_vectors")
@patch("matrixcurator_benchmark.setup.evaluation_services.setup_evaluators")
@patch("matrixcurator_benchmark.setup.dataset_services.sync_datasets", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.setup.dataset_services.preparse_documents", new_callable=AsyncMock)
async def test_bootstrap_environment_skip_targets(
    mock_preparse,
    mock_sync,
    mock_setup_evaluators,
    mock_auto_ingest
):
    mock_preparse.return_value = [{"document_id": "doc_1"}]
    
    docs_dict = await bootstrap_environment(limit=10, skip_sync=False, no_cache=False, targets=["retrieval"])
    
    mock_preparse.assert_called_once()
    mock_sync.assert_called_once()
    mock_setup_evaluators.assert_not_called()
    mock_auto_ingest.assert_called_once()
    
    assert "doc_1" in docs_dict
