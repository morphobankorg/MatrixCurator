from unittest.mock import patch, MagicMock
from matrixcurator.modules.nodes import parser_node, evaluator_node, supervisor_node

@patch("matrixcurator.modules.nodes.completion")
def test_parser_node_success(mock_completion):
    # Arrange
    mock_response = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "parse_with_txt"
    mock_response.choices = [MagicMock(message=MagicMock(tool_calls=[mock_tool_call]))]
    mock_completion.return_value = mock_response
    
    state = {
        "filename": "test.txt",
        "file_content": b"Hello world",
        "attempts": 0
    }
    
    # Act
    with patch("matrixcurator.modules.tools.txt.parse_with_txt.invoke", return_value="Hello world"):
        result = parser_node(state)
    
    # Assert
    assert result["parsed_text"] == "Hello world"
    assert result["current_tool"] == "parse_with_txt"
    assert result["attempts"] == 1

def test_evaluator_node_parsing_bad():
    state = {
        "parsed_text": "abc", # Too short
        "extracted_data": None
    }
    result = evaluator_node(state)
    assert result["evaluation_score"] == 5
    assert len(result["errors"]) == 1

def test_evaluator_node_extraction_good():
    state = {
        "parsed_text": "Some long text here...",
        "extracted_data": {
            "character_name": "Tail",
            "states": {"0": "short"}
        }
    }
    result = evaluator_node(state)
    assert result["evaluation_score"] == 10
    assert len(result["errors"]) == 0

def test_supervisor_node_routing():
    # Needs parsing
    state1 = {"parsed_text": None, "attempts": 0}
    assert supervisor_node(state1).goto == "parser_node"
    
    # Parsing failed, retry
    state2 = {"parsed_text": "abc", "evaluation_score": 5, "attempts": 1, "extracted_data": None}
    assert supervisor_node(state2).goto == "parser_node"
    
    # Parsing good, needs extraction
    state3 = {"parsed_text": "Good text", "evaluation_score": 10, "attempts": 1, "extracted_data": None}
    assert supervisor_node(state3).goto == "extractor_node"
    
    # Extraction failed, retry
    state4 = {"parsed_text": "Good text", "extracted_data": {"character_name": ""}, "evaluation_score": 5, "attempts": 1}
    assert supervisor_node(state4).goto == "extractor_node"
    
    # Extraction good, end
    state5 = {"parsed_text": "Good text", "extracted_data": {"character_name": "Tail", "states": {"0": "short"}}, "evaluation_score": 10, "attempts": 1}
    assert supervisor_node(state5).goto == "__end__"
