import pytest
from unittest.mock import patch, MagicMock
from matrixcurator.config.main import settings, OrchestrationStrategy, IntelligenceStrategy, ContextStrategy
from matrixcurator.modules.nodes import extraction_node, evaluation_node
from matrixcurator.modules.state import AgentState

@pytest.fixture
def mock_dspy_extraction():
    with patch('matrixcurator.modules.nodes.get_extraction_module') as mock_get:
        mock_module = MagicMock()
        mock_get.return_value = mock_module
        
        mock_result = MagicMock()
        mock_result.character = {"index": 1, "name": "From DSPy"}
        mock_result.states = []
        mock_module.return_value = mock_result
        yield mock_module

@pytest.fixture
def mock_litellm_extraction():
    with patch('matrixcurator.modules.nodes.extract_characters_and_states') as mock_ext:
        mock_result = MagicMock()
        
        mock_char = MagicMock()
        mock_char.index = 1
        mock_char.name = "From Prompt"
        
        mock_state = MagicMock()
        mock_state.character = mock_char
        mock_state.states = []
        
        mock_result.character_states = [mock_state]
        mock_ext.return_value = mock_result
        yield mock_ext

@pytest.fixture
def mock_retrieve_context():
    with patch('matrixcurator.modules.nodes.retrieve_context') as mock_ret:
        mock_ret.return_value = "Retrieved contextual chunk."
        yield mock_ret

@pytest.mark.asyncio
async def test_extraction_node_strategies(mock_dspy_extraction, mock_litellm_extraction, mock_retrieve_context):
    state: AgentState = {
        "document": {"text": {"default": "Full document text"}},
        "characters": {"1": [{"character": {"index": 1, "name": ""}, "states": [], "status": "pending"}]},
        "current_focus": "1"
    }
    
    # 1. Test PROGRAMMATIC_OPTIMIZATION (DSPy) + FULL_CONTEXT
    from matrixcurator.config.main import intelligence_strategy_var, context_strategy_var, orchestration_strategy_var
    intelligence_strategy_var.set(IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION)
    context_strategy_var.set(ContextStrategy.FULL_CONTEXT)
    
    cmd = await extraction_node(state)
    
    assert mock_dspy_extraction.called
    assert not mock_litellm_extraction.called
    assert not mock_retrieve_context.called
    
    attempts = cmd.update["characters"]["1"]
    assert attempts[-1]["character"]["name"] == "From DSPy"
    
    mock_dspy_extraction.reset_mock()
    mock_litellm_extraction.reset_mock()
    mock_retrieve_context.reset_mock()
    
    # 2. Test PROMPT_ENGINEERING (LiteLLM) + RETRIEVAL_AUGMENTED
    intelligence_strategy_var.set(IntelligenceStrategy.PROMPT_ENGINEERING)
    context_strategy_var.set(ContextStrategy.RETRIEVAL_AUGMENTED)
    
    cmd = await extraction_node(state)
    
    assert not mock_dspy_extraction.called
    assert mock_retrieve_context.called
    assert mock_litellm_extraction.called
    
    # It should have used the retrieved context
    mock_litellm_extraction.assert_called_once_with(text="Retrieved contextual chunk.", indices=[1])
    
    attempts = cmd.update["characters"]["1"]
    assert attempts[-1]["character"]["name"] == "From Prompt"

def test_evaluation_node_routing_strategies():
    state: AgentState = {
        "document": {"text": {"default": "Full text"}},
        "characters": {
            "1": [
                {"character": {"index": 1, "name": "test"}, "states": [], "status": "evaluating"}
            ]
        },
        "current_focus": "1"
    }
    
    with patch('matrixcurator.modules.nodes.get_evaluation_module') as mock_get:
        mock_eval = MagicMock()
        mock_get.return_value = mock_eval
        
        # Mock score < 8
        mock_result = MagicMock()
        mock_result.score = 5
        mock_result.reasoning = "Not good enough"
        mock_eval.return_value = mock_result
        
        # Test STATIC_ROUTING (Should approve despite low score)
        from matrixcurator.config.main import orchestration_strategy_var
        orchestration_strategy_var.set(OrchestrationStrategy.STATIC_ROUTING)
        cmd = evaluation_node(state)
        
        assert cmd.update["characters"]["1"][-1]["status"] == "approved"
        
        # Test DYNAMIC_ROUTING (Should pend for retry on low score)
        orchestration_strategy_var.set(OrchestrationStrategy.DYNAMIC_ROUTING)
        cmd = evaluation_node(state)
        
        assert cmd.update["characters"]["1"][-1]["status"] == "pending"
