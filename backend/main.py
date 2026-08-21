from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import engine, Base
from backend.api import meetings
from backend.config import get_settings

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Meeting Summarizer API",
    description="Backend service for Whisper ASR transcription and LLM structured meeting analysis.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)

@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend operational status."""
    settings = get_settings()
    return {
        "status": "online",
        "asr_provider": settings.ASR_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
        "database": settings.DATABASE_URL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
