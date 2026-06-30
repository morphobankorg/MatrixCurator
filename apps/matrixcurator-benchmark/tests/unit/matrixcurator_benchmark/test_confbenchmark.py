import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from matrixcurator_benchmark.confbenchmark import fixture_synced_langfuse
import matrixcurator_benchmark.modules.dataset.repositories.langfuse as dataset_langfuse_repository
import matrixcurator_benchmark.modules.evaluation.repositories.langfuse as evaluation_langfuse_repository
import matrixcurator_benchmark.modules.dataset.repositories.parquet as parquet_repo

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.confbenchmark.sync_datasets", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.confbenchmark.setup_evaluators")
async def test_fixture_synced_langfuse(mock_setup_evaluators, mock_sync_datasets):
    # Arrange
    skip_sync = False
    lf_client = MagicMock()
    fixture_parsed_cache = [{"id": "doc1"}]

    # Act
    # Calling the decorated async function directly
    result = await fixture_synced_langfuse(
        skip_sync=skip_sync,
        lf_client=lf_client,
        fixture_parsed_cache=fixture_parsed_cache
    )

    # Assert
    assert result is True
    
    # Assert sync_datasets was called with the correct dataset repository
    mock_sync_datasets.assert_called_once_with(
        parquet_repo,
        dataset_langfuse_repository,
        lf_client,
        fixture_parsed_cache
    )
    
    # Assert setup_evaluators was called with the correct evaluation repository
    mock_setup_evaluators.assert_called_once_with(
        evaluation_langfuse_repository,
        lf_client
    )

@pytest.mark.asyncio
@patch("matrixcurator_benchmark.confbenchmark.sync_datasets", new_callable=AsyncMock)
@patch("matrixcurator_benchmark.confbenchmark.setup_evaluators")
async def test_fixture_synced_langfuse_skip_sync(mock_setup_evaluators, mock_sync_datasets):
    # Arrange
    skip_sync = True
    lf_client = MagicMock()
    fixture_parsed_cache = [{"id": "doc1"}]

    # Act
    result = await fixture_synced_langfuse(
        skip_sync=skip_sync,
        lf_client=lf_client,
        fixture_parsed_cache=fixture_parsed_cache
    )

    # Assert
    assert result is True
    mock_sync_datasets.assert_not_called()
    mock_setup_evaluators.assert_not_called()
