from fastapi import APIRouter, HTTPException
from matrixcurator.modules.agent.schemas import ExtractRequest, ExtractResponse
from matrixcurator import MatrixCuratorClient

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
client = MatrixCuratorClient(app_name="fastapi-agent-router")

@router.post("/extract", response_model=ExtractResponse)
async def extract_data(request: ExtractRequest):
    try:
        result = await client.extract_characters(
            context=request.context,
            character_indices=request.character_indices,
            model_provider=request.model_provider,
            fallback_model=request.fallback_model,
            user_id=request.user_id
        )
        return ExtractResponse(
            extracted_states=result["extracted_states"], 
            errors=result["errors"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
