import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from src.benchmark.confbenchmark import setup_evaluators
from langfuse.api.unstable.evaluators import CreateEvaluatorRequest_LlmAsJudge

@patch("src.benchmark.confbenchmark.langfuse", create=True)
@patch.dict(os.environ, {"LANGFUSE_EVAL_PROVIDER": "custom-provider", "LANGFUSE_EVAL_MODEL": "custom-model"})
def test_setup_evaluators_custom_env(mock_langfuse_module):
    """
    Test that setup_evaluators correctly picks up custom environment variables.
    """
    mock_langfuse = MagicMock()
    mock_langfuse.api.score_configs.get.return_value.data = []
    mock_langfuse.get_dataset.return_value.id = "test-dataset-id"
    mock_langfuse.api.unstable.evaluation_rules.list.return_value.data = []

    setup_evaluators(mock_langfuse)

    mock_langfuse.api.unstable.evaluators.create.assert_called_once()
    create_call_args = mock_langfuse.api.unstable.evaluators.create.call_args[1]
    request_obj = create_call_args["request"]
    
    assert request_obj.model_config_.provider == "custom-provider"
    assert request_obj.model_config_.model == "custom-model"

@patch("src.benchmark.confbenchmark.langfuse", create=True)
def test_setup_evaluators_success(mock_langfuse_module):
    """
    Test that setup_evaluators correctly constructs the payload
    and calls the unstable evaluators create API.
    """
    mock_langfuse = MagicMock()
    
    # Mock score configs get
    mock_score_configs = MagicMock()
    mock_score_configs.data = []
    mock_langfuse.api.score_configs.get.return_value = mock_score_configs
    
    # Mock dataset ID
    mock_dataset = MagicMock()
    mock_dataset.id = "test-dataset-id"
    mock_langfuse.get_dataset.return_value = mock_dataset
    
    # Mock existing evaluation rules
    mock_rules_list = MagicMock()
    mock_rules_list.data = []
    mock_langfuse.api.unstable.evaluation_rules.list.return_value = mock_rules_list

    setup_evaluators(mock_langfuse)

    # Verify score config creation
    mock_langfuse.api.score_configs.create.assert_called_once()
    
    # Verify evaluator creation
    mock_langfuse.api.unstable.evaluators.create.assert_called_once()
    create_call_args = mock_langfuse.api.unstable.evaluators.create.call_args[1]
    
    # Assert that a CreateEvaluatorRequest_LlmAsJudge was passed
    request_obj = create_call_args["request"]
    assert isinstance(request_obj, CreateEvaluatorRequest_LlmAsJudge)
    assert request_obj.name == "Semantic Recall"
    assert request_obj.model_config_.provider == "google"
    assert request_obj.model_config_.model == "gemini-3.5-flash"
    
    # Assert that the new semantic entailment instructions are in the prompt
    assert "DO NOT penalize the Extracted Output for lacking JSON formatting" in request_obj.prompt
    assert "{{input}}" not in request_obj.prompt
    
    # Assert the output definition has the correct dict format for score
    output_def = request_obj.output_definition
    score_dump = output_def.score.model_dump() if hasattr(output_def.score, "model_dump") else output_def.score
    assert score_dump == {
        "description": "Select the best category label from the defined score config.",
        "categories": [
            "Complete Recall",
            "Recall Failure",
            "Partial Recall",
            "Semantic Corruption",
            "Low Context Precision"
        ],
        "should_allow_multiple_matches": False
    }

    # Verify evaluation rule creation
    mock_langfuse.api.unstable.evaluation_rules.create.assert_called_once()
    
    rule_create_args = mock_langfuse.api.unstable.evaluation_rules.create.call_args[1]
    rule_request = rule_create_args["request"]
    
    # Assert rule mapping does not contain 'input' anymore
    mapping_variables = [m.variable for m in rule_request.mapping]
    assert "input" not in mapping_variables
    assert "output" in mapping_variables
    assert "expected_output" in mapping_variables
