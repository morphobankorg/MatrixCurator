import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, InlineVlmOptions, InferenceFramework, TransformersModelType, TransformersPromptStyle, ResponseFormat
from docling.models.inference_engines.vlm.base import VlmEngineInput

from matrixcurator.integrations.docling import McpVlmEngine, McpVlmConvertModel
from matrixcurator.integrations.mcp import mcp_session_var
from matrixcurator.config.main import settings

@pytest.fixture
def mock_mcp_session():
    session = AsyncMock()
    
    # Create a mock MCP result
    mock_result = MagicMock()
    mock_result.role = "assistant"
    
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "MCP Docling Response"
    mock_result.content = [mock_content]
    
    session.create_message.return_value = mock_result
    return session

@pytest.fixture
def mock_vlm_input():
    input_data = MagicMock(spec=VlmEngineInput)
    input_data.prompt = "Describe this image"
    input_data.temperature = 0.5
    input_data.max_new_tokens = 100
    
    # Mock PIL Image
    mock_image = MagicMock()
    mock_image.copy.return_value = mock_image
    mock_image.convert.return_value = mock_image
    input_data.image = mock_image
    
    return input_data

def test_mcp_vlm_convert_model_forces_api_options():
    # Arrange
    mock_options = MagicMock()
    mock_options.engine_options = InlineVlmOptions(
        repo_id="test",
        inference_framework=InferenceFramework.TRANSFORMERS,
        response_format=ResponseFormat.MARKDOWN,
        prompt="test prompt"
    )
    mock_options.model_spec.prompt = "test prompt"
    mock_options.model_spec.response_format = ResponseFormat.MARKDOWN
    
    # Act
    with patch("matrixcurator.integrations.docling.VlmConvertModel.__init__") as mock_super_init:
        model = McpVlmConvertModel(enabled=True, options=mock_options, enable_remote_services=True, artifacts_path=None, accelerator_options=MagicMock())
        
        # Assert
        from docling.datamodel.vlm_engine_options import ApiVlmEngineOptions
        assert isinstance(mock_options.engine_options, ApiVlmEngineOptions)
        mock_super_init.assert_called_once()

@patch("matrixcurator.integrations.docling.completion")
def test_mcp_vlm_engine_litellm_fallback(mock_completion, mock_vlm_input):
    # Arrange
    options = ApiVlmOptions(url="http://localhost:8000", prompt="test", response_format=ResponseFormat.MARKDOWN)
    engine = McpVlmEngine(enable_remote_services=True, options=options)
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "LiteLLM fallback text"
    mock_completion.return_value = mock_response
    
    # Act
    result = engine.predict_batch([mock_vlm_input])
    
    # Assert
    mock_completion.assert_called_once()
    kwargs = mock_completion.call_args.kwargs
    assert kwargs["model"] == settings.vlm_model
    assert kwargs["temperature"] == 0.5
    assert kwargs["max_tokens"] == 100
    assert kwargs["messages"][0]["role"] == "user"
    assert len(kwargs["messages"][0]["content"]) == 2
    assert kwargs["messages"][0]["content"][0]["type"] == "image_url"
    assert "data:image/png;base64," in kwargs["messages"][0]["content"][0]["image_url"]["url"]
    assert kwargs["messages"][0]["content"][1]["type"] == "text"
    assert kwargs["messages"][0]["content"][1]["text"] == "Describe this image"
    
    assert len(result) == 1
    assert result[0].text == "LiteLLM fallback text"

@pytest.mark.asyncio
async def test_parse_with_docling_concurrency_and_cache():
    import asyncio
    import time
    from matrixcurator.modules.tools.docling import parse_with_docling
    import matrixcurator.modules.tools.docling
    
    # Reset globals
    matrixcurator.modules.tools.docling._converter = None
    matrixcurator.modules.tools.docling._manager = None
    
    call_count = 0
    
    class MockConverter:
        def __init__(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
        def convert(self, stream, **kwargs):
            time.sleep(0.1)  # Simulate slow work
            mock_res = MagicMock()
            mock_res.document.export_to_markdown.return_value = "parsed"
            return mock_res
            
    with patch("matrixcurator.modules.tools.docling.DocumentConverter", new=MockConverter):
        # We need to mock get_limiter so we can set an arbitrary max_concurrency
        mock_limiter = MagicMock()
        mock_limiter.max_concurrency = 3
        mock_limiter.acquire = AsyncMock()
        
        with patch("matrixcurator.modules.tools.docling.get_limiter", return_value=mock_limiter):
            # Fire 10 tasks concurrently
            tasks = [parse_with_docling.ainvoke({"file_content": b"dummy", "filename": f"file_{i}.pdf"}) for i in range(10)]
            
            start_time = time.monotonic()
            results = await asyncio.gather(*tasks)
            end_time = time.monotonic()
            
            # Since sleep is 0.1 and concurrency is 3, 10 tasks should take ceil(10/3)*0.1 = 0.4 seconds
            # Without concurrency manager, it would take 0.1 seconds because all would run in parallel
            assert end_time - start_time >= 0.3
            
            # Converter should only be instantiated EXACTLY once
            assert call_count == 1
            
            for res in results:
                assert res == "parsed"

@patch("matrixcurator.integrations.docling.sample_message")
def test_mcp_vlm_engine_predict_batch_mcp(mock_sample_message, mock_vlm_input, mock_mcp_session):
    # Arrange
    options = ApiVlmOptions(url="http://localhost:8000", prompt="test", response_format=ResponseFormat.MARKDOWN)
    engine = McpVlmEngine(enable_remote_services=True, options=options)
    
    token = mcp_session_var.set(mock_mcp_session)
    
    # Mock sample_message
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "MCP text"
    mock_result.content = [mock_content]
    
    async def mock_sample(*args, **kwargs):
        return mock_result
        
    mock_sample_message.side_effect = mock_sample
    
    try:
        # Act
        result = engine.predict_batch([mock_vlm_input])
        
        # Assert
        mock_sample_message.assert_called_once()
        assert len(result) == 1
        assert result[0].text == "MCP text"
    finally:
        mcp_session_var.reset(token)
