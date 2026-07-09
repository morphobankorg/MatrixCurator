import os
import pytest
from unittest.mock import patch, MagicMock

import dspy
from scripts.compile_state import (
    main,
    MODELS_TO_COMPILE,
)

@patch("scripts.compile_state.load_examples")
def test_main_no_examples(mock_load):
    # Arrange
    mock_load.return_value = []

    # Act
    main()

    # Assert
    # Script exits early, so we just ensure it doesn't crash


@patch("scripts.compile_state.load_examples")
@patch("scripts.compile_state.Path.exists")
@patch("scripts.compile_state.MIPROv2")
def test_main_skips_existing_weights(mock_miprov2, mock_exists, mock_load, monkeypatch):
    # Arrange
    # Provide dummy example so it passes `if not dataset:`
    mock_load.return_value = [dspy.Example(document_id="doc1")]
    # Force exists=True so it hits the skip branch
    mock_exists.return_value = True
    # Ensure FORCE_RECOMPILE is not 'true'
    monkeypatch.setenv("FORCE_RECOMPILE", "false")

    # Act
    main()

    # Assert
    mock_miprov2.assert_not_called()


@patch("scripts.compile_state.load_examples")
@patch("scripts.compile_state.Path.exists")
@patch("scripts.compile_state.MIPROv2")
def test_main_force_recompile(mock_miprov2, mock_exists, mock_load, monkeypatch):
    # Arrange
    mock_load.return_value = [dspy.Example(document_id="doc1")]
    # File exists, but FORCE_RECOMPILE bypasses it
    mock_exists.return_value = True
    monkeypatch.setenv("FORCE_RECOMPILE", "true")
    # For deterministic num_threads
    monkeypatch.setenv("DSPY_NUM_THREADS", "8")

    mock_teleprompter = MagicMock()
    mock_miprov2.return_value = mock_teleprompter

    # Act
    main()

    # Assert
    assert mock_miprov2.call_count == len(MODELS_TO_COMPILE)
    assert mock_teleprompter.compile.call_count == len(MODELS_TO_COMPILE)
    
    # Check if MIPROv2 was called with num_threads=8 and required models
    for call in mock_miprov2.call_args_list:
        args, kwargs = call
        if "num_threads" in kwargs:
            assert kwargs["num_threads"] == 8
        assert "prompt_model" in kwargs
        assert "task_model" in kwargs


@patch("scripts.compile_state.load_examples")
@patch("scripts.compile_state.Path.exists")
@patch("scripts.compile_state.MIPROv2")
def test_main_pipeline_success(mock_miprov2, mock_exists, mock_load, monkeypatch):
    # Arrange
    mock_load.return_value = [dspy.Example(document_id="doc1")]
    # Ensure weights don't exist
    def exists_side_effect():
        return False
    mock_exists.side_effect = exists_side_effect
    monkeypatch.setenv("FORCE_RECOMPILE", "false")
    monkeypatch.setenv("DSPY_NUM_THREADS", "12")

    mock_teleprompter = MagicMock()
    mock_compiled_student = MagicMock()
    mock_teleprompter.compile.return_value = mock_compiled_student
    mock_miprov2.return_value = mock_teleprompter

    # Act
    main()

    # Assert
    assert mock_miprov2.call_count == len(MODELS_TO_COMPILE)
    assert mock_teleprompter.compile.call_count == len(MODELS_TO_COMPILE)
    assert mock_compiled_student.save.call_count == len(MODELS_TO_COMPILE)

    # Assert the call arguments for MIPROv2 include num_threads and models
    miprov2_kwargs = mock_miprov2.call_args.kwargs
    assert "num_threads" in miprov2_kwargs
    assert miprov2_kwargs["num_threads"] == 12
    assert "prompt_model" in miprov2_kwargs
    assert "task_model" in miprov2_kwargs
