from typing import List, Dict, Any, Optional
from matrixcurator.modules.document.services import parse_document, generate_document
from matrixcurator.modules.agent.graph import agent_graph
from matrixcurator.config.main import Settings, settings as global_settings
from python_logging.main import get_logger
from matrixcurator.integrations.posthog import capture_event
import uuid

__all__ = ["MatrixCuratorClient"]

class MatrixCuratorClient:
    def __init__(self, app_name: str = "matrixcurator", **kwargs: Any):
        if kwargs:
            new_settings = Settings(**kwargs)
            for key, value in new_settings.model_dump(exclude_unset=True).items():
                setattr(global_settings, key, value)
                
        self.logger = get_logger(__name__)
        self.logger.info(f"Initialized MatrixCuratorClient for {app_name}")

    def parse_document(self, content: bytes, filename: str) -> str:
        """Parses a document and returns the extracted text."""
        self.logger.info(f"Parsing document: {filename}")
        text = parse_document(content, filename)
        capture_event("document_parsed", {"filename": filename})
        return text

    async def extract_characters(
        self,
        context: str,
        character_indices: List[int],
        starting_tier: int = 2,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extracts character states from the given context."""
        extracted_states = []
        all_errors = []
        
        self.logger.info(f"Extracting characters: {character_indices} starting at tier {starting_tier}")
        
        for idx in character_indices:
            thread_id = str(uuid.uuid4())
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "starting_tier": starting_tier,
                    "user_id": user_id
                }
            }
            
            initial_state = {
                "character_index": idx,
                "context": context,
                "current_tier": starting_tier,
                "attempts": 0,
                "errors": []
            }
            
            try:
                result = await agent_graph.ainvoke(initial_state, config)
                
                if result.get("extracted_data"):
                    extracted_states.append(result["extracted_data"])
                if result.get("errors"):
                    all_errors.extend(result["errors"])
                    
            except Exception as e:
                error_msg = f"Failed to extract character {idx}: {str(e)}"
                self.logger.error(error_msg)
                all_errors.append(error_msg)
                
        capture_event("characters_extracted", {"num_indices": len(character_indices), "starting_tier": starting_tier})
        return {"extracted_states": extracted_states, "errors": all_errors}

    def generate_nexus(self, original_nexus: str, extracted_states: List[Dict[str, Any]]) -> bytes:
        """Generates an updated NEXUS file with the extracted states."""
        self.logger.info("Generating updated NEXUS file")
        updated_nexus_bytes = generate_document(
            original_nexus=original_nexus,
            extracted_states=extracted_states
        )
        capture_event("nexus_generated")
        return updated_nexus_bytes
