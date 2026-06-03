from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.modules.document.router import router as document_router
from src.modules.agent.router import router as agent_router
from src.config.main import settings

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

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
