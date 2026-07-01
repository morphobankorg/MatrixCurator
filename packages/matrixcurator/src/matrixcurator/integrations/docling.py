import asyncio
import base64
import logging
import time
from io import BytesIO
from typing import List


from docling.models.inference_engines.vlm.api_openai_compatible_engine import (
    ApiVlmEngine,
)
from docling.models.inference_engines.vlm.base import VlmEngineInput, VlmEngineOutput
from docling.models.stages.vlm_convert.vlm_convert_model import VlmConvertModel
from docling.pipeline.vlm_pipeline import VlmPipeline, VlmPipelineOptions

from matrixcurator.integrations.mcp import (
    MCPSamplingError,
    mcp_session_var,
    sample_message,
)
from matrixcurator.integrations.litellm import completion
from matrixcurator.config.main import settings

logger = logging.getLogger(__name__)


class McpVlmEngine(ApiVlmEngine):
    """
    Custom VLM Engine for Docling that intercepts calls for MCP sampling.
    Falls back to litellm.completion (Gemini) if no MCP session is active or if sampling fails.
    """

    def predict_batch(self, input_batch: List[VlmEngineInput]) -> List[VlmEngineOutput]:
        session = mcp_session_var.get()
        outputs = []

        for input_data in input_batch:
            # Format image and prompt for MCP/LiteLLM
            img_io = BytesIO()
            image = input_data.image.copy().convert("RGBA")
            image.save(img_io, "PNG")
            image_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                        {"type": "text", "text": input_data.prompt},
                    ],
                }
            ]

            request_start_time = time.time()
            content = ""

            if session is not None:
                # Execute MCP sampling synchronously
                try:
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    if loop.is_running():
                        logger.warning(
                            "Cannot run sync MCP sampling inside an active event loop. Falling back to native LiteLLM."
                        )
                        raise RuntimeError("Event loop is already running")

                    mcp_result = loop.run_until_complete(
                        sample_message(
                            session=session,
                            messages=messages,
                            temperature=input_data.temperature,
                            max_tokens=input_data.max_new_tokens,
                        )
                    )

                    # Extract text content
                    if hasattr(mcp_result, "content"):
                        for item in mcp_result.content:
                            if getattr(item, "type", "") == "text":
                                content += getattr(item, "text", "")

                except MCPSamplingError as e:
                    logger.warning(
                        f"MCP sampling failed, falling back to native LiteLLM: {e}"
                    )
                    session = None  # Trigger fallback
                except Exception as e:
                    logger.warning(
                        f"Unexpected error during MCP sampling, falling back to native LiteLLM: {e}"
                    )
                    session = None  # Trigger fallback

            if session is None:
                # Fallback to LiteLLM (Gemini)
                try:
                    response = completion(
                        model=settings.vlm_model,
                        messages=messages,
                        temperature=input_data.temperature,
                        max_tokens=input_data.max_new_tokens,
                    )
                    content = response.choices[0].message.content or ""
                except Exception as e:
                    logger.error(f"LiteLLM fallback failed: {e}")
                    content = ""

            generation_time = time.time() - request_start_time

            outputs.append(
                VlmEngineOutput(
                    text=content,
                    stop_reason="stop",
                    metadata={
                        "generation_time": generation_time,
                        "num_tokens": 0,
                    },
                )
            )

        return outputs


class McpVlmConvertModel(VlmConvertModel):
    """
    Custom VlmConvertModel that injects McpVlmEngine.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace the engine with our MCP-aware engine
        # Note: VlmConvertModel uses self.options.engine_options
        if hasattr(self, "options") and hasattr(self.options, "engine_options"):
            self.engine = McpVlmEngine(
                enable_remote_services=getattr(self, "enable_remote_services", True),
                options=self.options.engine_options,
            )


class McpVlmPipeline(VlmPipeline):
    """
    Custom VlmPipeline that uses McpVlmConvertModel.
    """

    def _initialize_new_runtime_system(
        self, pipeline_options: VlmPipelineOptions
    ) -> None:
        try:
            from docling.datamodel.vlm_engine_options import (
                ApiVlmEngineOptions,
                VlmEngineType,
            )

            if (
                not getattr(pipeline_options.vlm_options, "engine_options", None)
                or getattr(pipeline_options.vlm_options.engine_options, "engine_type", None)
                != VlmEngineType.API_OLLAMA
            ):
                pipeline_options.vlm_options.engine_options = ApiVlmEngineOptions(
                    engine_type=VlmEngineType.API_OLLAMA,
                    url="http://localhost:11434/v1/chat/completions",
                )
        except ImportError:
            from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions

            if not isinstance(pipeline_options.vlm_options.engine_options, ApiVlmOptions):
                pipeline_options.vlm_options.engine_options = ApiVlmOptions(
                    prompt=getattr(pipeline_options.vlm_options, "model_spec", pipeline_options.vlm_options).prompt,
                    response_format=getattr(pipeline_options.vlm_options, "model_spec", pipeline_options.vlm_options).response_format,
                )

        super()._initialize_new_runtime_system(pipeline_options)

        # Replace VlmConvertModel with McpVlmConvertModel in the build pipe
        for i, model in enumerate(self.build_pipe):
            if isinstance(model, VlmConvertModel):
                self.build_pipe[i] = McpVlmConvertModel(
                    enabled=True,
                    enable_remote_services=self.pipeline_options.enable_remote_services,
                    artifacts_path=self.artifacts_path,
                    options=pipeline_options.vlm_options,
                    accelerator_options=self.pipeline_options.accelerator_options,
                )
                logger.info("Injected McpVlmConvertModel into Docling pipeline")
