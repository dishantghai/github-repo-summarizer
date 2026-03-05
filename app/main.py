import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title="GitHub Repository Summarizer",
    description="API service to summarize GitHub repositories using LLMs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "GitHub Repository Summarizer",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "llm_configured": bool(settings.NEBIUS_API_KEY or settings.OPENAI_API_KEY),
        "github_token_configured": bool(settings.GITHUB_TOKEN),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
