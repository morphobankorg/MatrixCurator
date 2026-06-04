from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.fastapi.src.routers.document import router as document_router
from apps.fastapi.src.routers.agent import router as agent_router
from matrixcurator.config.main import settings
from matrixcurator.config.logging import setup_logging, get_logger
from matrixcurator.integrations.posthog import capture_event

# Initialize logging and telemetry
setup_logging(app_name="fastapi")
logger = get_logger(__name__)

app = FastAPI(
    title="MatrixCurator API",
    description="API for MatrixCurator document parsing and agent extraction",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the Streamlit app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_router)
app.include_router(agent_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting MatrixCurator API")
    capture_event("api_started")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.fastapi.src.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
