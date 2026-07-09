import os
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

import dspy
from scripts.compile_state import (
    extraction_metric,
    load_examples,
)


@patch("scripts.compile_state.EvaluationModule")
def test_extraction_metric(mock_eval_module_class):
    # Arrange
    mock_eval_module = MagicMock()
    mock_eval_module_class.return_value = mock_eval_module

    # Mock the return result of the EvaluationModule
    mock_result = MagicMock()
    mock_result.score = 8
    mock_eval_module.return_value = mock_result

    example = dspy.Example(
        document_text="Sample text",
        character_index=1,
        character={"name": "Test Character"},
        states=["State 1", "State 2"],
    )

    pred = dspy.Prediction(
        character_name="Test Character",
        states=["State 1", "State 2"],
    )

    # Act
    score = extraction_metric(example, pred)

    # Assert
    assert score == 0.8
    mock_eval_module.assert_called_once_with(
        document_text="Sample text",
        extracted_data={
            "character": "Test Character",
            "states": ["State 1", "State 2"],
            "expected_character": {
                "index": 1,
                "name": "Test Character",
            },
            "expected_states": ["State 1", "State 2"],
        },
    )


@patch("scripts.compile_state.pd.read_parquet")
@patch("scripts.compile_state.Path.exists")
def test_load_examples_page_filtering(mock_exists, mock_read_parquet):
    # Arrange
    mock_exists.return_value = True

    df_docs = pd.DataFrame(
        [
            {
                "id": "doc1",
                "text": json.dumps(
                    [
                        {
                            "parser": "docling",
                            "pages": [
                                {"page": 1, "content": "Page 1 target"},
                                {"page": 2, "content": "Page 2 skip"},
                            ],
                        }
                    ]
                ),
            },
            {
                "id": "doc2",
                "text": json.dumps(
                    [
                        {
                            "parser": "pymupdf",
                            "pages": [
                                {"page": 1, "content": "Doc 2 Page 1 fallback"},
                                {"page": 2, "content": "Doc 2 Page 2 fallback"},
                            ],
                        }
                    ]
                ),
            },
        ]
    )

    df_chars = pd.DataFrame(
        [
            {
                "document_id": "doc1",
                "character": json.dumps({"index": 1, "name": "Test Char 1"}),
                "states": json.dumps(["State A"]),
                "pages": json.dumps([1]),  # Filter to only page 1
            },
            {
                "document_id": "doc2",
                "character": json.dumps({"index": 2, "name": "Test Char 2"}),
                "states": json.dumps(["State B"]),
                "pages": None,  # No filter, should fallback to all pages
            },
        ]
    )

    def read_parquet_side_effect(path):
        if "documents.parquet" in str(path):
            return df_docs
        elif "character_states.parquet" in str(path):
            return df_chars
        raise ValueError(f"Unexpected path: {path}")

    mock_read_parquet.side_effect = read_parquet_side_effect

    # Act
    examples = load_examples()

    # Assert
    assert len(examples) == 2
    
    # Doc 1: Only target page 1
    ex1 = next(ex for ex in examples if ex.document_id == "doc1")
    assert ex1.document_text == "Page 1 target"
    assert ex1.character_index == 1
    
    # Doc 2: All pages
    ex2 = next(ex for ex in examples if ex.document_id == "doc2")
    assert "Doc 2 Page 1 fallback" in ex2.document_text
    assert "Doc 2 Page 2 fallback" in ex2.document_text
    assert ex2.document_text == "Doc 2 Page 1 fallback\n\nDoc 2 Page 2 fallback"
    assert ex2.character_index == 2


@patch("scripts.compile_state.Path.exists")
def test_load_examples_missing_files(mock_exists):
    # Arrange
    mock_exists.return_value = False

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="Benchmark parquet files not found"):
        load_examples()
