from langfuse import Langfuse
import os
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import time
import random
from typing import Optional, Dict, Any
from .external_service import GeminiService
from .exceptions import log_execution, handle_exceptions
from src.config.main import settings


class ExtractionEvaluationService:

    def __init__(self, extraction_model: str, evaluation_model: str, total_characters: int, zero_indexed: Optional[bool] = False, context: Optional[str] = None, context_upload: Optional[BytesIO] = None):
        self.extraction_model = extraction_model
        self.evaluation_model = evaluation_model
        self.context = context if context is not None else None
        self.context_upload = context_upload if context_upload is not None else None
        self.total_characters = total_characters
        self.zero_indexed = zero_indexed if zero_indexed is not None else False
        self.langfuse_client = self._langfuse_client()
        self.system_prompt = self.langfuse_client.get_prompt("system_prompt").prompt
        self.extraction_prompt = self.langfuse_client.get_prompt("extraction_prompt").prompt
        self.evaluation_prompt = self.langfuse_client.get_prompt("evaluation_prompt").prompt
        self.gemini_service = self._gemini_service()

    @log_execution
    @handle_exceptions
    def _langfuse_client(self) -> Langfuse:

        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY") or st.secrets["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.getenv("LANGFUSE_SECRET_KEY") or st.secrets["LANGFUSE_SECRET_KEY"],
            host=os.getenv("LANGFUSE_HOST") or st.secrets["LANGFUSE_HOST"],
        )
    
        return langfuse_client

    @log_execution
    @handle_exceptions   
    def _gemini_service(self):
        
        if self.context is not None:
            gemini_service = GeminiService(extraction_model=self.extraction_model, evaluation_model=self.evaluation_model, system_prompt=self.system_prompt, context=self.context)
            return gemini_service

        elif self.context_upload is not None:
            gemini_service = GeminiService(extraction_model=self.extraction_model, evaluation_model=self.evaluation_model, system_prompt=self.system_prompt, context_upload=self.context_upload)
            return gemini_service

    def _cycle(self, character_index) -> Optional[Dict[str, Any]]:
        character_index_dict = {"character_index": character_index}
        
        extraction_prompt = self.extraction_prompt.format(character_index=character_index)
        
        max_attempts = 5
        base_delay = 1
        attempt = 0
        
        while attempt <= max_attempts:
            try:
                # Attempt the extraction
                extraction_response = self.gemini_service.extract(prompt=extraction_prompt)
            
                # Attempt the evaluation
                evaluation_prompt = self.evaluation_prompt.format(
                    user_query=extraction_response, 
                    generated_answer=extraction_response
                )
                evaluation_response = self.gemini_service.evaluate(prompt=evaluation_prompt)
                
                if evaluation_response["score"] >= 8:
                    response = {**character_index_dict, **extraction_response, **evaluation_response}
                    return response
                else:
                    # If score is low, we'll try again with modified prompt
                    attempt += 1
                    extraction_prompt = extraction_prompt + f"\nAttempt {attempt}: {extraction_response}"
                    
            except Exception as e:  # You should catch specific exceptions here
                if "429" in str(e).lower() or "exceeded your current quota" in str(e).lower():
                    # Exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 60)  # Max 60 seconds
                    time.sleep(delay)
                    continue
                else:
                    continue
        
        print(f"Failed after {max_attempts} attempts")
        return None

    @log_execution
    @handle_exceptions
    def run_cycle(self, progress_callback=None) -> tuple[list[dict], list[int]]:
        with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
            futures = []
            start_index = 0 if self.zero_indexed else 1
            end_index = self.total_characters
            total_tasks = end_index - start_index + 1

            # Submit all tasks
            for character_index in range(start_index, end_index + 1):
                future = executor.submit(self._cycle, character_index)
                futures.append((character_index, future))

            successful_results = []
            failed_indexes = []
            
            # Process results with progress updates
            for i, (character_index, future) in enumerate(futures):
                result = future.result()
                if result is None:
                    failed_indexes.append(character_index)
                else:
                    successful_results.append(result)
                
                # Update progress if callback provided
                if progress_callback:
                    progress = (i + 1) / total_tasks
                    progress_callback(progress)

            return successful_results, failed_indexes