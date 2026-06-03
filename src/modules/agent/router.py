from fastapi import APIRouter, HTTPException
from src.modules.agent.schemas import ExtractRequest, ExtractResponse
from src.modules.agent.graph import agent_graph
from src.config.main import settings
import uuid

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

@router.post("/extract", response_model=ExtractResponse)
async def extract_data(request: ExtractRequest):
    extracted_states = []
    all_errors = []
    
    model = request.model_provider or settings.DEFAULT_MODEL
    
    for idx in request.character_indices:
        thread_id = str(uuid.uuid4())
        config = {
            "configurable": {
                "thread_id": thread_id,
                "model_provider": model,
                "fallback_model": request.fallback_model or settings.FALLBACK_MODEL,
                "user_id": request.user_id
            }
        }
        
        initial_state = {
            "character_index": idx,
            "context": request.context,
            "current_model": model,
            "attempts": 0,
            "errors": []
        }
        
        try:
            # Run the graph
            result = await agent_graph.ainvoke(initial_state, config)
            
            if result.get("extracted_data"):
                extracted_states.append(result["extracted_data"])
            if result.get("errors"):
                all_errors.extend(result["errors"])
                
        except Exception as e:
            all_errors.append(f"Failed to extract character {idx}: {str(e)}")
            
    return ExtractResponse(extracted_states=extracted_states, errors=all_errors)
