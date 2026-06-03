import pytest
from src.modules.document.repositories.nexus import read_nexus, write_nexus
from src.exceptions import NexusFormatError

def test_nexus_repository_read():
    content = b"Hello NEXUS"
    result = read_nexus(content)
    assert result == "Hello NEXUS"

def test_nexus_repository_write_success(sample_nexus):
    extracted_states = [
        {
            "character_index": 1,
            "character_name": "Eye color",
            "states": {"0": "blue", "1": "brown"}
        },
        {
            "character_index": 2,
            "character_name": "Hair color",
            "states": {"0": "blonde", "1": "black"}
        }
    ]
    
    result_bytes = write_nexus(sample_nexus, extracted_states)
    result_str = result_bytes.decode("utf-8")
    
    assert "CHARSTATELABELS" in result_str
    assert "1 'Eye color' / 0 'blue', 1 'brown'," in result_str
    assert "2 'Hair color' / 0 'blonde', 1 'black'" in result_str
    assert "MATRIX" in result_str
    
    # Ensure CHARSTATELABELS is before MATRIX
    assert result_str.find("CHARSTATELABELS") < result_str.find("MATRIX")

def test_nexus_repository_write_missing_matrix():
    with pytest.raises(NexusFormatError) as exc_info:
        write_nexus("BEGIN TAXA; END;", [])
        
    assert "MATRIX block not found" in str(exc_info.value)

def test_nexus_repository_write_special_characters(sample_nexus):
    extracted_states = [
        {
            "character_index": 1,
            "character_name": "Bird's wing",
            "states": {"0": "doesn't fly", "1": "flies"}
        }
    ]
    
    result_bytes = write_nexus(sample_nexus, extracted_states)
    result_str = result_bytes.decode("utf-8")
    
    # Check that single quotes are escaped as double single quotes
    assert "1 'Bird''s wing' / 0 'doesn''t fly', 1 'flies'" in result_str
