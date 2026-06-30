import pytest
import json
from unittest.mock import MagicMock

from matrixcurator_benchmark.benchmark_tools import (
    skip_non_pdf,
    skip_non_docx,
    skip_non_txt,
    _execute_tool_benchmark,
)
from matrixcurator_benchmark.core.exceptions import SkipBenchmark, FailBenchmark

class MockDatasetItem:
    def __init__(self, input_data):
        self.input = input_data

def test_skip_conditions():
    # PDF
    kwargs_pdf = {
        "dataset_item": MockDatasetItem({"document_id": "pdf_doc"}),
        "docs_dict": {"pdf_doc": {"mime_type": "application/pdf"}}
    }
    assert skip_non_pdf(kwargs_pdf) is False
    assert skip_non_docx(kwargs_pdf) is True
    assert skip_non_txt(kwargs_pdf) is True

    # DOCX
    kwargs_docx = {
        "dataset_item": MockDatasetItem({"document_id": "docx_doc"}),
        "docs_dict": {"docx_doc": {"mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}}
    }
    assert skip_non_pdf(kwargs_docx) is True
    assert skip_non_docx(kwargs_docx) is False
    assert skip_non_txt(kwargs_docx) is True

    # TXT
    kwargs_txt = {
        "dataset_item": MockDatasetItem({"document_id": "txt_doc"}),
        "docs_dict": {"txt_doc": {"mime_type": "text/plain"}}
    }
    assert skip_non_pdf(kwargs_txt) is True
    assert skip_non_docx(kwargs_txt) is True
    assert skip_non_txt(kwargs_txt) is False

    # Missing doc
    kwargs_missing = {
        "dataset_item": MockDatasetItem({"document_id": "missing_doc"}),
        "docs_dict": {}
    }
    assert skip_non_pdf(kwargs_missing) is True
    assert skip_non_docx(kwargs_missing) is True
    assert skip_non_txt(kwargs_missing) is True


@pytest.mark.asyncio
async def test_execute_tool_benchmark_success():
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": [
                {"page": 1, "content": "Page 1 content"},
                {"page": 2, "content": "Page 2 content"}
            ]
        }
    ]
    
    dataset_item = MockDatasetItem({"document_id": "doc2", "pages": [1, 2]})
    docs_dict = {"doc2": {"mime_type": "application/pdf", "text": json.dumps(pre_parsed_data)}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="TestTool",
        parser=parser,
        default_ext="pdf",
        requires_pages=True,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )

    langfuse_trace.assert_called_once_with("Page 1 content\n\nPage 2 content")
    parser.invoke.assert_not_called()


@pytest.mark.asyncio
async def test_execute_tool_benchmark_missing_text():
    dataset_item = MockDatasetItem({"document_id": "doc3", "pages": [3]})
    docs_dict = {"doc3": {"mime_type": "application/pdf", "text": None}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    with pytest.raises(FailBenchmark, match="TestTool parsing failed: missing text in parquet cache for doc doc3"):
        await _execute_tool_benchmark(
            dataset_item=dataset_item,
            tool_name="TestTool",
            parser=parser,
            default_ext="pdf",
            requires_pages=True,
            docs_dict=docs_dict,
            langfuse_trace=langfuse_trace,
        )

    parser.invoke.assert_not_called()

@pytest.mark.asyncio
async def test_execute_tool_benchmark_missing_page():
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": [
                {"page": 1, "content": "Page 1 content"}
            ]
        }
    ]
    dataset_item = MockDatasetItem({"document_id": "doc3", "pages": [1, 3]})
    docs_dict = {"doc3": {"mime_type": "application/pdf", "text": json.dumps(pre_parsed_data)}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    with pytest.raises(FailBenchmark, match="TestTool parsing failed: Could not find valid parsed content for required pages."):
        await _execute_tool_benchmark(
            dataset_item=dataset_item,
            tool_name="TestTool",
            parser=parser,
            default_ext="pdf",
            requires_pages=True,
            docs_dict=docs_dict,
            langfuse_trace=langfuse_trace,
        )

    parser.invoke.assert_not_called()

@pytest.mark.asyncio
async def test_execute_tool_benchmark_success_with_list():
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": [
                {"page": 1, "content": "Page 1 list content"},
            ]
        }
    ]
    
    dataset_item = MockDatasetItem({"document_id": "doc_list", "pages": [1]})
    docs_dict = {"doc_list": {"mime_type": "application/pdf", "text": pre_parsed_data}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="TestTool",
        parser=parser,
        default_ext="pdf",
        requires_pages=True,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )

    langfuse_trace.assert_called_once_with("Page 1 list content")
    parser.invoke.assert_not_called()


@pytest.mark.asyncio
async def test_execute_tool_benchmark_missing_text_empty_list():
    dataset_item = MockDatasetItem({"document_id": "doc_empty", "pages": [1]})
    docs_dict = {"doc_empty": {"mime_type": "application/pdf", "text": []}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    with pytest.raises(FailBenchmark, match="TestTool parsing failed: missing text in parquet cache for doc doc_empty"):
        await _execute_tool_benchmark(
            dataset_item=dataset_item,
            tool_name="TestTool",
            parser=parser,
            default_ext="pdf",
            requires_pages=True,
            docs_dict=docs_dict,
            langfuse_trace=langfuse_trace,
        )


@pytest.mark.asyncio
async def test_execute_tool_benchmark_nan_handling():
    import numpy as np
    dataset_item = MockDatasetItem({"document_id": "doc_nan", "pages": [1]})
    docs_dict = {"doc_nan": {"mime_type": "application/pdf", "text": np.nan}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    with pytest.raises(FailBenchmark, match="TestTool parsing failed: missing text in parquet cache for doc doc_nan"):
        await _execute_tool_benchmark(
            dataset_item=dataset_item,
            tool_name="TestTool",
            parser=parser,
            default_ext="pdf",
            requires_pages=True,
            docs_dict=docs_dict,
            langfuse_trace=langfuse_trace,
        )


@pytest.mark.asyncio
async def test_execute_tool_benchmark_handles_numpy_pages():
    import numpy as np
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": [
                {"page": 1, "content": "Page 1 numpy content"},
                {"page": "2", "content": "Page 2 string content"}
            ]
        }
    ]
    
    # Use numpy.int64 values for pages as they would come from a pandas dataframe
    dataset_item = MockDatasetItem({"document_id": "doc_numpy", "pages": np.array([1, 2], dtype=np.int64)})
    docs_dict = {"doc_numpy": {"mime_type": "application/pdf", "text": pre_parsed_data}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    await _execute_tool_benchmark(
        dataset_item=dataset_item,
        tool_name="TestTool",
        parser=parser,
        default_ext="pdf",
        requires_pages=True,
        docs_dict=docs_dict,
        langfuse_trace=langfuse_trace,
    )

    langfuse_trace.assert_called_once_with("Page 1 numpy content\n\nPage 2 string content")
    parser.invoke.assert_not_called()

@pytest.mark.asyncio
async def test_execute_tool_benchmark_doc_not_found():
    dataset_item = MockDatasetItem({"document_id": "missing"})
    docs_dict = {}
    
    with pytest.raises(SkipBenchmark, match="Document missing not found"):
        await _execute_tool_benchmark(
            dataset_item=dataset_item,
            tool_name="TestTool",
            parser=MagicMock(),
            default_ext="pdf",
            requires_pages=True,
            docs_dict=docs_dict,
            langfuse_trace=MagicMock(),
        )

@pytest.mark.asyncio
async def test_execute_tool_benchmark_null_pages():
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": None
        }
    ]
    
    dataset_item = MockDatasetItem({"document_id": "doc_null", "pages": [1]})
    docs_dict = {"doc_null": {"mime_type": "application/pdf", "text": pre_parsed_data}}
    langfuse_trace = MagicMock()
    parser = MagicMock()

    with pytest.raises(FailBenchmark, match="TestTool parsing failed: Could not find valid parsed content for required pages."):
        await _execute_tool_benchmark(
            dataset_item=dataset_item,
            tool_name="TestTool",
            parser=parser,
            default_ext="pdf",
            requires_pages=True,
            docs_dict=docs_dict,
            langfuse_trace=langfuse_trace,
        )

    parser.invoke.assert_not_called()

