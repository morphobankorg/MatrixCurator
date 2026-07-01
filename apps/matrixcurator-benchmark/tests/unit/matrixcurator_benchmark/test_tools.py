import pytest
import json
from matrixcurator_benchmark.tools import tool_task, filter_tool_items

class MockDatasetItem:
    def __init__(self, input_data):
        self.input = input_data

def test_filter_tool_items_skip_wrong_mime():
    dataset_item = MockDatasetItem({"document_id": "pdf_doc"})
    docs_dict = {"pdf_doc": {"mime_type": "text/plain"}}
    assert not filter_tool_items(dataset_item, "application/pdf", docs_dict)

def test_filter_tool_items_doc_not_found():
    dataset_item = MockDatasetItem({"document_id": "missing"})
    docs_dict = {}
    assert not filter_tool_items(dataset_item, "application/pdf", docs_dict)

@pytest.mark.asyncio
async def test_tool_task_success():
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

    result = await tool_task(
        item=dataset_item,
        tool_name="TestTool",
        requires_pages=True,
        docs_dict=docs_dict,
    )

    assert result == "Page 1 content\n\nPage 2 content"


@pytest.mark.asyncio
async def test_tool_task_missing_text():
    dataset_item = MockDatasetItem({"document_id": "doc3", "pages": [3]})
    docs_dict = {"doc3": {"mime_type": "application/pdf", "text": None}}

    with pytest.raises(ValueError, match="TestTool parsing failed: missing text in parquet cache for doc doc3"):
        await tool_task(
            item=dataset_item,
            tool_name="TestTool",
            requires_pages=True,
            docs_dict=docs_dict,
        )


@pytest.mark.asyncio
async def test_tool_task_missing_page():
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

    with pytest.raises(ValueError, match="TestTool parsing failed: Could not find valid parsed content for required pages."):
        await tool_task(
            item=dataset_item,
            tool_name="TestTool",
            requires_pages=True,
            docs_dict=docs_dict,
        )


@pytest.mark.asyncio
async def test_tool_task_success_with_list():
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

    result = await tool_task(
        item=dataset_item,
        tool_name="TestTool",
        requires_pages=True,
        docs_dict=docs_dict,
    )

    assert result == "Page 1 list content"


@pytest.mark.asyncio
async def test_tool_task_missing_text_empty_list():
    dataset_item = MockDatasetItem({"document_id": "doc_empty", "pages": [1]})
    docs_dict = {"doc_empty": {"mime_type": "application/pdf", "text": []}}

    with pytest.raises(ValueError, match="TestTool parsing failed: missing text in parquet cache for doc doc_empty"):
        await tool_task(
            item=dataset_item,
            tool_name="TestTool",
            requires_pages=True,
            docs_dict=docs_dict,
        )


@pytest.mark.asyncio
async def test_tool_task_nan_handling():
    import numpy as np
    dataset_item = MockDatasetItem({"document_id": "doc_nan", "pages": [1]})
    docs_dict = {"doc_nan": {"mime_type": "application/pdf", "text": np.nan}}

    with pytest.raises(ValueError, match="TestTool parsing failed: missing text in parquet cache for doc doc_nan"):
        await tool_task(
            item=dataset_item,
            tool_name="TestTool",
            requires_pages=True,
            docs_dict=docs_dict,
        )


@pytest.mark.asyncio
async def test_tool_task_handles_numpy_pages():
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
    
    dataset_item = MockDatasetItem({"document_id": "doc_numpy", "pages": np.array([1, 2], dtype=np.int64)})
    docs_dict = {"doc_numpy": {"mime_type": "application/pdf", "text": pre_parsed_data}}

    result = await tool_task(
        item=dataset_item,
        tool_name="TestTool",
        requires_pages=True,
        docs_dict=docs_dict,
    )

    assert result == "Page 1 numpy content\n\nPage 2 string content"


@pytest.mark.asyncio
async def test_tool_task_resilient_input_parsing():
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": [
                {"page": 1, "content": "Page 1 content"}
            ]
        }
    ]
    
    docs_dict = {
        "doc1": {"mime_type": "application/pdf", "text": pre_parsed_data},
        "doc2": {"mime_type": "application/pdf", "text": pre_parsed_data},
        "doc3": {"mime_type": "application/pdf", "text": pre_parsed_data},
    }
    
    # 1. Dict input
    item1 = MockDatasetItem({"document_id": "doc1", "pages": [1]})
    
    # 2. Object input
    class ObjInput:
        document_id = "doc2"
        pages = [1]
    item2 = MockDatasetItem(ObjInput())
    
    # 3. JSON string input
    item3 = MockDatasetItem('{"document_id": "doc3", "pages": [1]}')
    
    for item in [item1, item2, item3]:
        result = await tool_task(
            item=item,
            tool_name="TestTool",
            requires_pages=True,
            docs_dict=docs_dict,
        )
        assert result == "Page 1 content"


@pytest.mark.asyncio
async def test_tool_task_null_pages():
    pre_parsed_data = [
        {
            "parser": "testtool",
            "pages": [
                {"page": 1, "content": "Page 1 content"},
                {"page": 2, "content": "Page 2 content"}
            ]
        }
    ]
    
    # Send missing/null pages
    dataset_item = MockDatasetItem({"document_id": "doc_null", "pages": []})
    docs_dict = {"doc_null": {"mime_type": "application/pdf", "text": pre_parsed_data}}

    result = await tool_task(
        item=dataset_item,
        tool_name="TestTool",
        requires_pages=True,
        docs_dict=docs_dict,
    )
    
    # Should resolve both pages
    assert result == "Page 1 content\n\nPage 2 content"
