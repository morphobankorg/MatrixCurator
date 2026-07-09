import os
import pytest
import vcr
from unittest.mock import patch

import dspy
from scripts.compile_state import main

my_vcr = vcr.VCR(
    serializer="yaml",
    cassette_library_dir="scripts/tests/e2e/cassettes",
    record_mode="once",
    match_on=["uri", "method"],
    filter_headers=["Authorization", "api-key"],
)

@pytest.mark.e2e
@patch("scripts.compile_state.MODELS_TO_COMPILE", ["gemini/gemini-3.1-flash-lite"])
@patch("scripts.compile_state.load_examples")
def test_compile_state(mock_load, monkeypatch):
    # Arrange
    # Provide 2 dummy examples to satisfy train/val splits quickly
    ex1 = dspy.Example(
        document_id="doc1",
        document_text="The quick brown fox jumps over the lazy dog.",
        character_index=1,
        character={"name": "Fox", "index": 1},
        states=["Jumps"],
        previous_errors=None,
    ).with_inputs("document_text", "character_index", "previous_errors")
    
    ex2 = dspy.Example(
        document_id="doc2",
        document_text="A fast dog chases the fox.",
        character_index=2,
        character={"name": "Dog", "index": 2},
        states=["Chases"],
        previous_errors=None,
    ).with_inputs("document_text", "character_index", "previous_errors")
    
    mock_load.return_value = [ex1, ex2]

    # Force configurations for deterministic and fast E2E test
    from matrixcurator.config.main import settings
    monkeypatch.setattr(settings, "max_examples", 2)
    monkeypatch.setenv("FORCE_RECOMPILE", "true")
    monkeypatch.setenv("DSPY_NUM_THREADS", "1")
    monkeypatch.setenv("DSPY_AUTO", "none")
    monkeypatch.setattr(settings, "telemetry_opt_out", True)
    monkeypatch.setattr(settings, "num_trials", 1)
    monkeypatch.setattr(settings, "num_candidates", 3)
    monkeypatch.setattr(settings, "minibatch_size", 10)
    monkeypatch.setattr(settings, "max_bootstrapped_demos", 3)
    monkeypatch.setattr(settings, "max_labeled_demos", 4)
    
    # We also want to patch out the minibatch to ensure deterministic VCR recording.
    # We can do this by patching MIPROv2.compile to override its kwargs, or we just rely on DSPY_NUM_THREADS=1.
    # DSPY_NUM_THREADS=1 already enforces single-threaded execution, making VCR stable.

    # Act
    from litellm import ModelResponse, Message, Choices
    
    mock_resp = ModelResponse(
        id="mock_id", 
        choices=[Choices(finish_reason="stop", index=0, message=Message(content="Mocked response", role="assistant"))], 
        model="mock",
        usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
    )
    
    with patch("matrixcurator.integrations.litellm.completion", return_value=mock_resp), \
         patch("matrixcurator.integrations.litellm.acompletion", return_value=mock_resp):
        # We need to catch or let it run, we expect it completes successfully
        main()

    # Assert
    # Check if the output JSON was created in the weights directory
    output_path = "packages/matrixcurator/src/matrixcurator/weights/gemini-3.1-flash-lite.json"
    assert os.path.exists(output_path), f"Expected compiled weights at {output_path}"
