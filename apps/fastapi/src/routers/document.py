from fastapi import APIRouter, UploadFile, File, HTTPException
from matrixcurator.modules.document.schemas import ParseResponse, NexusGenerateRequest, NexusGenerateResponse
from matrixcurator.exceptions import DocumentParseError, NexusFormatError
from matrixcurator import MatrixCuratorClient

router = APIRouter(prefix="/api/v1/document", tags=["document"])
client = MatrixCuratorClient(app_name="fastapi-document-router")

@router.post("/parse", response_model=ParseResponse)
async def parse_document_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename
    
    try:
        text = client.parse_document(content, filename)
        return ParseResponse(text=text)
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nexus", response_model=NexusGenerateResponse)
async def generate_nexus_endpoint(request: NexusGenerateRequest):
    try:
        updated_nexus_bytes = client.generate_nexus(
            original_nexus=request.original_nexus,
            extracted_states=request.extracted_states
        )
        return NexusGenerateResponse(updated_nexus=updated_nexus_bytes.decode("utf-8"))
    except NexusFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
