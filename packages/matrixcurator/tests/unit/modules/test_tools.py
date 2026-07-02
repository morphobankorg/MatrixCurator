import pytest
from unittest.mock import patch, MagicMock
from matrixcurator.modules.tools.pymupdf import parse_with_pymupdf
from matrixcurator.modules.tools.txt import parse_with_txt
from matrixcurator.modules.tools.re import generate_with_re
from matrixcurator.modules.tools.docling import parse_with_docling
from matrixcurator.exceptions import DocumentParseError

@pytest.mark.asyncio
@patch("matrixcurator.modules.tools.pymupdf.fitz.open")
async def test_pymupdf_tool_success(mock_fitz_open):
    mock_doc = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 text. "
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 text."
    
    mock_doc.__iter__.return_value = [mock_page1, mock_page2]
    mock_fitz_open.return_value = mock_doc
    
    content = b"fake pdf content"
    
    result = await parse_with_pymupdf.ainvoke({"file_content": content, "filename": "test.pdf"})
    
    assert result == "Page 1 text. Page 2 text."
    mock_fitz_open.assert_called_once_with(stream=content, filetype="pdf")

@pytest.mark.asyncio
@patch("matrixcurator.modules.tools.pymupdf.fitz.open")
async def test_pymupdf_tool_page_filtering(mock_fitz_open):
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 3
    
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 text. "
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 text. "
    mock_page3 = MagicMock()
    mock_page3.get_text.return_value = "Page 3 text."
    
    mock_doc.__getitem__.side_effect = lambda i: [mock_page1, mock_page2, mock_page3][i]
    mock_fitz_open.return_value = mock_doc
    
    content = b"fake pdf content"
    
    result = await parse_with_pymupdf.ainvoke({"file_content": content, "filename": "test.pdf", "pages": [1, 3]})
    
    assert result == "Page 1 text. Page 3 text."

@pytest.mark.asyncio
@patch("matrixcurator.modules.tools.pymupdf.fitz.open")
async def test_pymupdf_tool_failure(mock_fitz_open):
    mock_fitz_open.side_effect = Exception("Corrupted PDF")
    content = b"corrupted pdf content"
    
    with pytest.raises(DocumentParseError) as exc_info:
        await parse_with_pymupdf.ainvoke({"file_content": content, "filename": "test.pdf"})
    
    assert "Failed to parse PDF with PyMuPDF: Corrupted PDF" in str(exc_info.value)

@pytest.mark.asyncio
async def test_txt_tool_success():
    content = b"Hello world"
    result = await parse_with_txt.ainvoke({"file_content": content, "filename": "test.txt"})
    assert result == "Hello world"

def test_re_tool_success():
    original_nexus = "BEGIN DATA;\nDIMENSIONS NTAX=3 NCHAR=1;\nFORMAT DATATYPE=STANDARD MISSING=? GAP=-;\nMATRIX\nTaxonA 1\nTaxonB 0\nTaxonC ?\n;\nEND;"
    extracted_states = [
        {
            "character_index": 1,
            "character_name": "Tail length",
            "states": {"0": "short", "1": "long"}
        }
    ]
    
    result = generate_with_re.invoke({"original_nexus": original_nexus, "extracted_states": extracted_states})
    result_str = result.decode("utf-8")
    
    assert "CHARSTATELABELS" in result_str
    assert "1 'Tail length' / 0 'short', 1 'long'" in result_str
    assert "MATRIX" in result_str

@pytest.mark.asyncio
@patch("matrixcurator.modules.tools.docling.DocumentConverter")
async def test_docling_tool_success(mock_converter_class):
    mock_converter = MagicMock()
    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = "Docling parsed text"
    mock_converter.convert.return_value = mock_result
    mock_converter_class.return_value = mock_converter
    
    content = b"fake doc content"
    result = await parse_with_docling.ainvoke({"file_content": content, "filename": "test.pdf"})
    
    assert result == "Docling parsed text"
    
    # Assert DocumentConverter was initialized with the correct format_options
    mock_converter_class.assert_called_once()
    kwargs = mock_converter_class.call_args.kwargs
    assert "format_options" in kwargs
    
    from docling.datamodel.document import InputFormat
    from matrixcurator.integrations.docling import McpVlmPipeline
    
    format_options = kwargs["format_options"]
    assert InputFormat.PDF in format_options
    pdf_option = format_options[InputFormat.PDF]
    assert pdf_option.pipeline_cls == McpVlmPipeline
    
    mock_converter.convert.assert_called_once()

@pytest.mark.asyncio
@patch("matrixcurator.modules.tools.docling.DocumentConverter")
async def test_docling_tool_page_filtering(mock_converter_class):
    mock_converter = MagicMock()
    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = "Docling parsed text"
    mock_converter.convert.return_value = mock_result
    mock_converter_class.return_value = mock_converter
    
    content = b"fake doc content"
    result = await parse_with_docling.ainvoke({"file_content": content, "filename": "test.pdf", "pages": [2, 4]})
    
    assert result == "Docling parsed text"
    mock_converter.convert.assert_called_once()
    kwargs = mock_converter.convert.call_args.kwargs
    assert kwargs.get("page_range") == (2, 4)
