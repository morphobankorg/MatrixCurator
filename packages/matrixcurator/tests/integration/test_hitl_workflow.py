import pytest
import uuid
from unittest.mock import patch, MagicMock
from langgraph.errors import NodeInterrupt
from matrixcurator.modules.graph import build_graph
from matrixcurator.config.main import settings, OrchestrationStrategy

@pytest.fixture
def hitl_graph():
    return build_graph()

@patch("matrixcurator.modules.nodes.parse_document")
@patch("matrixcurator.modules.nodes.get_discovery_module")
@patch("matrixcurator.modules.nodes.get_extraction_module")
@patch("matrixcurator.modules.nodes.get_evaluation_module")
def test_full_hitl_workflow(mock_eval, mock_extract, mock_discover, mock_parse, hitl_graph):
    # Setup mocks
    mock_parse.return_value = "Full parsed document text here."
    
    discover_res = MagicMock()
    discover_res.inferred_pages = [1, 2]
    discover_res.total_characters = 1 # Just 1 character for testing
    discover_res.confidence = 0.9
    mock_discover.return_value.return_value = discover_res
    
    extract_res = MagicMock()
    extract_res.character = {"index": 1, "name": "Tail"}
    extract_res.states = [{"index": 0, "name": "absent"}]
    mock_extract.return_value.return_value = extract_res
    
    eval_res = MagicMock()
    eval_res.score = 5 # Force failure
    eval_res.reasoning = "Missed state 1"
    mock_eval.return_value.return_value = eval_res
    
    settings.orchestration_strategy = OrchestrationStrategy.DYNAMIC_ROUTING
    
    # 1. Start graph
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "document": {
            "file_bytes": b"fake pdf content",
            "filename": "test.pdf",
            "status": "pending"
        }
    }
    
    # Run the graph until it hits the interrupt (3 failed attempts = human_review)
    # The graph will run:
    # supervisor -> document_node -> supervisor -> extraction -> evaluation -> supervisor -> extraction -> evaluation -> supervisor -> extraction -> evaluation -> supervisor (INTERRUPT)
    
    try:
        hitl_graph.invoke(initial_state, config=config)
    except Exception as e:
        # Some versions of LangGraph propagate NodeInterrupt, others catch it and pause the thread.
        pass
        
    # 2. Check the state at the interrupt
    state_snapshot = hitl_graph.get_state(config)
    
    # 3 extraction attempts should be logged
    attempts = state_snapshot.values["characters"]["1"]
    assert len(attempts) == 3
    assert attempts[-1]["status"] == "human_review"
    
    # 3. Simulate human fixing the data and approving it
    # We construct a new list of attempts where the last one is approved, or we append a new one
    human_approved_attempt = {
        "character": {"index": 1, "name": "Tail"},
        "states": [{"index": 0, "name": "absent"}, {"index": 1, "name": "present"}], # Human fixed it
        "score": 10,
        "evaluator_reasoning": "Human approved",
        "status": "approved"
    }
    
    updated_attempts = attempts + [human_approved_attempt]
    
    # Update the graph state
    hitl_graph.update_state(config, {"characters": {"1": updated_attempts}})
    
    # 4. Resume the graph
    # Supervisor will see it is approved and move to __end__
    final_state = hitl_graph.invoke(None, config=config)
    
    assert final_state["characters"]["1"][-1]["status"] == "approved"
    assert len(final_state["characters"]["1"]) == 4 # 3 failed + 1 human approved
