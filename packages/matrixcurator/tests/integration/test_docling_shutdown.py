import subprocess
import sys

def test_docling_shutdown_is_clean():
    """
    Tests that when a Python process imports and initializes the Docling DocumentConverter, 
    it can shut down cleanly without emitting 'ImportError: sys.meta_path is None' 
    or 'Exception ignored in: <function VlmConvertModel.__del__'.
    """
    # Create a small script that initializes the converter and exits
    script = """
import logging
logging.basicConfig(level=logging.INFO)
from matrixcurator.modules.tools.docling import get_converter

# Trigger the singleton initialization
converter = get_converter()
print("Converter initialized successfully")
"""
    
    # Run the script in a subprocess
    result = subprocess.run(
        [sys.executable, "-c", script], 
        capture_output=True, 
        text=True
    )
    
    # Assert successful execution
    assert result.returncode == 0, f"Process failed with stderr: {result.stderr}"
    
    # Assert no shutdown traceback warnings in stderr
    assert "Exception ignored in" not in result.stderr
    assert "sys.meta_path is None" not in result.stderr
