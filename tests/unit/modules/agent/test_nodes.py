import pytest
from unittest.mock import patch, MagicMock
from src.modules.agent.nodes import extractor_agent, evaluator_agent, supervisor_node, llm_error_handler
from src.exceptions import ContextLengthExceededError

@patch("src.modules.agent.nodes.completion")
def test_extractor_agent_success(mock_completion):
    # Arrange
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"character_index": 1, "character_name": "Eye color", "states": {"0": "blue"}}'
    mock_completion.return_value = mock_response
    
    state = {
        "character_index": 1,
        "context": "Eye color is blue (0).",
        "current_model": "test-model",
        "attempts": 0
    }
    
    # Act
    result = extractor_agent(state)
    
    # Assert
    assert result["extracted_data"]["character_name"] == "Eye color"
    assert result["attempts"] == 1
    mock_completion.assert_called_once()

def test_extractor_agent_empty_context():
    state = {
        "character_index": 1,
        "context": "",
        "current_model": "test-model",
        "attempts": 0
    }
    
    result = extractor_agent(state)
    assert result["extracted_data"] is None
    assert "Empty context provided." in result["errors"]

def test_extractor_agent_context_too_large():
    state = {
        "character_index": 1,
        "context": "a" * 1000001,
        "current_model": "test-model",
        "attempts": 0
    }
    
    with pytest.raises(ContextLengthExceededError):
        extractor_agent(state)

def test_evaluator_agent_good_data():
    state = {
        "extracted_data": {
            "character_name": "Eye color",
            "states": {"0": "blue"}
        }
    }
    
    result = evaluator_agent(state)
    assert result["evaluation_score"] == 10

def test_evaluator_agent_missing_data():
    state = {
        "extracted_data": {
            "character_name": "",
            "states": {}
        }
    }
    
    result = evaluator_agent(state)
    assert result["evaluation_score"] == 0

def test_supervisor_node_retry():
    state = {
        "extracted_data": None,
        "evaluation_score": 0,
        "attempts": 1
    }
    
    command = supervisor_node(state)
    assert command.goto == "extractor_agent"

def test_supervisor_node_end():
    state = {
        "extracted_data": {"some": "data"},
        "evaluation_score": 10,
        "attempts": 1
    }
    
    command = supervisor_node(state)
    assert command.goto == "__end__"

def test_supervisor_node_max_attempts():
    state = {
        "extracted_data": None,
        "evaluation_score": 0,
        "attempts": 3
    }
    
    command = supervisor_node(state)
    assert command.goto == "__end__"
