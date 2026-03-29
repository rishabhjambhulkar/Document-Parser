from fastapi import FastAPI
from app.api.routes import router as api_router
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.core.config import settings
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Asynchronous Document Processing API
    
    This API allows you to:
    * **Submit documents** for asynchronous processing.
    * **Track job status** and retrieve results.
    * **List all jobs** with pagination.
    
    The backend uses **Celery** with **Redis** as a broker and **MongoDB** for persistence.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    logger.info("Application starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    logger.info("Application shutting down...")

app.include_router(api_router, prefix="/api/v1")

@app.get(
    "/",
    tags=["health"],
    responses={
        200: {
            "description": "API status and info",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Welcome to the Document Processing API",
                        "status": "active",
                        "docs": "/docs",
                        "version": "1.0.0"
                    }
                }
            }
        }
    }
)
async def root():
    """Root endpoint to check API status."""
    return {
        "message": "Welcome to the Document Processing API",
        "status": "active",
        "docs": "/docs",
        "version": "1.0.0"
    }
