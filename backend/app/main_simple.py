"""
Minimal FastAPI application for testing.
"""
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="Chat With Documents – RAG System",
    description="AI-powered PDF question answering",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {
        "name": "Chat With Documents – RAG System",
        "version": "0.1.0",
        "docs": "/docs",
    }

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {"api": "healthy"},
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
