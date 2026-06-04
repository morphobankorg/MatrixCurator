import pytest
from matrixcurator.modules.document.repositories.txt import read_txt

def test_txt_repository_read():
    content = b"Hello World"
    result = read_txt(content)
    assert result == "Hello World"
