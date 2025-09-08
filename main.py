
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from routers.auth import router as auth_router
from routers.workflow import router as workflow_router

# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = FastAPI(
    title="S3 Download, Auto-Commit & Approve PR Workflow",
    description="Automates S3 downloads, GitHub commits, and PR approvals using FastAPI, AWS S3, and GitHub MCP.",
    version="0.1.0"
)

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(workflow_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("uvicorn.access")
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/")
def root():
    return {
        "app": app.title,
        "description": app.description,
        "version": app.version,
        "docs_url": "/docs",
        "health_url": "/health"
    }
