import os
import streamlit as st
from typing import Optional, Union
from google import genai
from google.genai import types
import json
from io import BytesIO
import base64
from .exceptions import log_execution, handle_exceptions

class GeminiService:
    def __init__(self, extraction_model: str, evaluation_model: str, system_prompt: str, context: Optional[str] = None, context_upload: Optional[BytesIO] = None):

        self.api_key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
        self.client = genai.Client(
            api_key=self.api_key,
        )
        self.extraction_model = extraction_model
        self.evaluation_model = evaluation_model
        self.system_prompt = system_prompt
        self.context = context if context is not None else None
        self.context_base64 = self._context_base64(file=context_upload) if context_upload is not None else None
        self.context_upload = self._context_upload(file=context_upload) if context_upload is not None else None
        self.extraction_context_cache = self._cache(model=extraction_model)
        self.evaluation_context_cache = self._cache(model=evaluation_model)
    
    @log_execution
    @handle_exceptions
    def _cache(self, model) -> Union[None, types.CachedContent]:

        if self.context is not None:
            content = self.context
        elif self.context_upload is not None:
            content = self.context_upload
        
        try:
            cache = self.client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                system_instruction=(str(self.system_prompt)),
                contents=[content],
                ttl="3600s",
            )
        )
            return cache
        
        except:
            return None
    
    @log_execution
    @handle_exceptions
    def _context_base64(self, file: BytesIO) -> dict:

        file_bytes = file.getvalue()

        file_base64 = base64.b64encode(file_bytes).decode("utf-8")

        return file_base64

    @log_execution
    @handle_exceptions
    def _context_upload(self, file: BytesIO) -> types.File:

        context_upload = self.client.files.upload(
            file=file,
            config=dict(
                mime_type='application/pdf'
            )
        )

        return context_upload

    @handle_exceptions
    def extract(self, prompt: str) -> str:
        
        model = self.extraction_model
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=str(prompt)),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["character", "states"],
                properties = {
                    "character": genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                    "states": genai.types.Schema(
                        type = genai.types.Type.ARRAY,
                        items = genai.types.Schema(
                            type = genai.types.Type.STRING,
                        ),
                    ),
                },
            ),
        )
        
        # Add cached content to config if available
        if self.extraction_context_cache is not None:
            generate_content_config.cached_content = self.extraction_context_cache.name
        elif self.context is not None:
            # If no cache, include the full content in the request
            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text=self.context),
                    ],
                )
            )
        elif self.context_upload is not None:
            # Add uploaded file to the request
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                        mime_type="application/pdf",
                        data=base64.b64decode(str(self.context_base64)),
                        ),
                    ],
                ),
            )

        # Collect all chunks
        full_response = ""
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                full_response += chunk.text
        
        # Add Decorator
        return json.loads(full_response)

    @handle_exceptions
    def evaluate(self, prompt: str):
        
        model = self.evaluation_model
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=str(prompt)),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(

            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["score", "justification"],
                properties = {
                    "score": genai.types.Schema(
                        type = genai.types.Type.INTEGER,
                    ),
                    "justification": genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                },
            ),
        )
        
        # Add cached content to config if available
        if self.evaluation_context_cache is not None:
            generate_content_config.cached_content = self.evaluation_context_cache.name
        elif self.context is not None:
            # If no cache, include the full content in the request
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=self.context),
                    ],
                )
            )
        elif self.context_upload is not None:
            # Add uploaded file to the request
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                        mime_type="application/pdf",
                        data=base64.b64decode(str(self.context_base64)),
                        ),
                    ],
                ),
            )

        # Collect all chunks
        full_response = ""
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                full_response += chunk.text
        
        # Add exception decorator
        return json.loads(full_response)