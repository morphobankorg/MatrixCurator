import pytest
import sys
import os
import pandas as pd
sys.path.insert(0, os.path.abspath("."))
from unittest.mock import MagicMock, patch
from src.benchmark.tools_benchmark import docling_task, pymupdf_task, docx_task, txt_task

@pytest.fixture
def mock_df_docs():
    return pd.DataFrame([
        {"id": "doc1", "file_bytes": b"fake_pdf_bytes", "filename": "doc1.pdf", "mime_type": "application/pdf"}
    ])

@pytest.fixture
def mock_docs_dict(mock_df_docs):
    return mock_df_docs.set_index('id').to_dict(orient='index')

@pytest.fixture
def mock_df_docx():
    return pd.DataFrame([
        {"id": "doc2", "file_bytes": b"fake_docx_bytes", "filename": "doc2.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    ])

@pytest.fixture
def mock_docs_dict_docx(mock_df_docx):
    return mock_df_docx.set_index('id').to_dict(orient='index')

@pytest.fixture
def mock_df_txt():
    return pd.DataFrame([
        {"id": "doc3", "file_bytes": b"fake_txt_bytes", "filename": "doc3.txt", "mime_type": "text/plain"}
    ])

@pytest.fixture
def mock_docs_dict_txt(mock_df_txt):
    return mock_df_txt.set_index('id').to_dict(orient='index')

def test_docling_task_cache_hit(mock_docs_dict):
    mock_item = MagicMock()
    mock_item.input = {
        "document_id": "doc1",
        "pages": [1, 2]
    }
    
    cache = {
        ("doc1", (1, 2)): "Cached Docling Output"
    }
    
    result = docling_task(item=mock_item, docs_dict=mock_docs_dict, cache=cache)
    assert result == "Cached Docling Output"

@patch("src.benchmark.tools_benchmark.parse_with_docling")
def test_docling_task_cache_miss(mock_tool, mock_docs_dict):
    mock_tool.invoke.return_value = "Parsed Docling Output"
    
    mock_item = MagicMock()
    mock_item.input = {
        "document_id": "doc1",
        "pages": [1, 2]
    }
    
    cache = {}
    
    result = docling_task(item=mock_item, docs_dict=mock_docs_dict, cache=cache)
    
    assert result == "Parsed Docling Output"
    assert cache[("doc1", (1, 2))] == "Parsed Docling Output"
    mock_tool.invoke.assert_called_once_with({
        "file_content": b"fake_pdf_bytes",
        "filename": "doc1.pdf",
        "pages": [1, 2]
    })

def test_pymupdf_task_cache_hit(mock_docs_dict):
    mock_item = MagicMock()
    mock_item.input = {
        "document_id": "doc1",
        "pages": [1]
    }
    
    cache = {
        ("doc1", (1,)): "Cached PyMuPDF Output"
    }
    
    result = pymupdf_task(item=mock_item, docs_dict=mock_docs_dict, cache=cache)
    assert result == "Cached PyMuPDF Output"

@patch("src.benchmark.tools_benchmark.parse_with_pymupdf")
def test_pymupdf_task_cache_miss(mock_tool, mock_docs_dict):
    mock_tool.invoke.return_value = "Parsed PyMuPDF Output"
    
    mock_item = MagicMock()
    mock_item.input = {
        "document_id": "doc1",
        "pages": [1]
    }
    
    cache = {}
    
    result = pymupdf_task(item=mock_item, docs_dict=mock_docs_dict, cache=cache)
    
    assert result == "Parsed PyMuPDF Output"
    assert cache[("doc1", (1,))] == "Parsed PyMuPDF Output"
    mock_tool.invoke.assert_called_once_with({
        "file_content": b"fake_pdf_bytes",
        "filename": "doc1.pdf",
        "pages": [1]
    })

def test_docling_task_skip(mock_docs_dict_docx):
    mock_item = MagicMock()
    mock_item.input = {"document_id": "doc2", "pages": [1]}
    result = docling_task(item=mock_item, docs_dict=mock_docs_dict_docx, cache={})
    assert result == "Skipped: Not a PDF file"

def test_pymupdf_task_skip(mock_docs_dict_docx):
    mock_item = MagicMock()
    mock_item.input = {"document_id": "doc2", "pages": [1]}
    result = pymupdf_task(item=mock_item, docs_dict=mock_docs_dict_docx, cache={})
    assert result == "Skipped: Not a PDF file"

def test_docx_task_cache_hit(mock_docs_dict_docx):
    mock_item = MagicMock()
    mock_item.input = {
        "document_id": "doc2",
        "pages": [1]
    }
    
    cache = {
        ("doc2", (1,)): "Cached DOCX Output"
    }
    
    result = docx_task(item=mock_item, docs_dict=mock_docs_dict_docx, cache=cache)
    assert result == "Cached DOCX Output"

@patch("src.benchmark.tools_benchmark.parse_with_docx")
def test_docx_task_cache_miss(mock_tool, mock_docs_dict_docx):
    mock_tool.invoke.return_value = "Parsed DOCX Output"
    
    mock_item = MagicMock()
    mock_item.input = {
        "document_id": "doc2",
        "pages": [1]
    }
    
    cache = {}
    
    result = docx_task(item=mock_item, docs_dict=mock_docs_dict_docx, cache=cache)
    
    assert result == "Parsed DOCX Output"
    assert cache[("doc2", (1,))] == "Parsed DOCX Output"
    mock_tool.invoke.assert_called_once_with({
        "file_content": b"fake_docx_bytes",
        "filename": "doc2.docx"
    })

def test_docx_task_skip(mock_docs_dict):
    mock_item = MagicMock()
    mock_item.input = {"document_id": "doc1"}
    result = docx_task(item=mock_item, docs_dict=mock_docs_dict, cache={})
    assert result == "Skipped: Not a DOCX file"

def test_txt_task_cache_hit(mock_docs_dict_txt):
    mock_item = MagicMock()
    mock_item.input = {"document_id": "doc3", "pages": [1]}
    cache = {("doc3", (1,)): "Cached TXT Output"}
    result = txt_task(item=mock_item, docs_dict=mock_docs_dict_txt, cache=cache)
    assert result == "Cached TXT Output"

@patch("src.benchmark.tools_benchmark.parse_with_txt")
def test_txt_task_cache_miss(mock_tool, mock_docs_dict_txt):
    mock_tool.invoke.return_value = "Parsed TXT Output"
    mock_item = MagicMock()
    mock_item.input = {"document_id": "doc3", "pages": [1]}
    cache = {}
    
    result = txt_task(item=mock_item, docs_dict=mock_docs_dict_txt, cache=cache)
    assert result == "Parsed TXT Output"
    assert cache[("doc3", (1,))] == "Parsed TXT Output"
    mock_tool.invoke.assert_called_once_with({
        "file_content": b"fake_txt_bytes",
        "filename": "doc3.txt"
    })

def test_txt_task_skip(mock_docs_dict):
    mock_item = MagicMock()
    mock_item.input = {"document_id": "doc1"}
    result = txt_task(item=mock_item, docs_dict=mock_docs_dict, cache={})
    assert result == "Skipped: Not a TXT file"

from src.benchmark.tools_benchmark import process_benchmark

def test_process_benchmark_skips_runs():
    df_mixed = pd.DataFrame([
        {"id": "doc1", "mime_type": "application/pdf"},
        {"id": "doc2", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        {"id": "doc3", "mime_type": "text/plain"}
    ])
    
    item1 = MagicMock()
    item1.input = {"document_id": "doc1"}
    item2 = MagicMock()
    item2.input = {"document_id": "doc2"}
    item3 = MagicMock()
    item3.input = {"document_id": "doc3"}
    
    mock_langfuse = MagicMock()
    mock_dataset = MagicMock()
    mock_dataset.items = [item1, item2, item3]
    
    def side_effect_run_experiment(*args, **kwargs):
        name = kwargs.get('name')
        if name in ["Parser-Docling-Run", "Parser-PyMuPDF-Run"]:
            assert len(mock_dataset.items) == 1
            assert mock_dataset.items[0].input["document_id"] == "doc1"
        elif name == "Parser-DOCX-Run":
            assert len(mock_dataset.items) == 1
            assert mock_dataset.items[0].input["document_id"] == "doc2"
        elif name == "Parser-TXT-Run":
            assert len(mock_dataset.items) == 1
            assert mock_dataset.items[0].input["document_id"] == "doc3"
            
    mock_dataset.run_experiment.side_effect = side_effect_run_experiment
    
    process_benchmark(langfuse=mock_langfuse, dataset=mock_dataset, df_docs=df_mixed)
    
    assert mock_dataset.run_experiment.call_count == 4
    
    # Assert items are restored
    assert len(mock_dataset.items) == 3
