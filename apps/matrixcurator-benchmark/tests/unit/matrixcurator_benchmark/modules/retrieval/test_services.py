import sys
from unittest.mock import MagicMock
sys.modules["sqlite_vec"] = MagicMock()

import pytest
import pandas as pd
from unittest.mock import patch, AsyncMock
from matrixcurator_benchmark.modules.retrieval.services import auto_ingest_vectors


@patch("matrixcurator_benchmark.modules.retrieval.services.core_settings")
@patch("matrixcurator_benchmark.modules.retrieval.services.vectorize_document", new_callable=AsyncMock)
def test_auto_ingest_vectors_delegates_to_core(mock_vectorize, mock_settings):
    mock_settings.retrieval_backend = "sqlite"

    df_docs = pd.DataFrame([
        {
            "id": "doc_1",
            "text": [{"parser": "docling", "pages": [{"page": 1, "content": "text1"}]}],
            "pages": "[1, 2]"
        },
        {
            "id": "doc_2",
            "text": [{"parser": "docling", "pages": [{"page": 3, "content": "text3"}]}],
            "pages": [3]
        },
        {
            "id": "doc_3",
            "text": None,  # Should be skipped
            "pages": None
        }
    ])

    with patch("matrixcurator.modules.retrieval.repositories.sqlite.get_engine"):
        with patch("sqlalchemy.orm.Session") as mock_session:
            mock_session.return_value.__enter__.return_value.execute.return_value = [] # DB empty
            auto_ingest_vectors(df_docs)

    assert mock_vectorize.call_count == 2
    
    # Check first doc
    call1 = mock_vectorize.call_args_list[0]
    assert call1[0][0] == "doc_1"
    assert call1[0][2] == [1, 2] # string literal parsed successfully

    # Check second doc
    call2 = mock_vectorize.call_args_list[1]
    assert call2[0][0] == "doc_2"
    assert call2[0][2] == [3] # list preserved
