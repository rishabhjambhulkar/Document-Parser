from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, Path, status
from app.models.job import Job, JobCreate
from app.api.dependencies import rate_limiter, get_repository
from app.services.job_service import JobService
from typing import List, Optional

router = APIRouter(tags=["jobs"])

# Helper function to get the JobService
def get_job_service(repository = Depends(get_repository)):
    return JobService(repository)


# ── Example responses for OpenAPI docs ──────────────────────────────────────

_job_created_example = {
    "description": "Job successfully created and queued",
    "content": {
        "application/json": {
            "examples": {
                "url_submission": {
                    "summary": "Job from document URL",
                    "value": {
                        "_id": "664f1a2b3c4d5e6f7a8b9c0d",
                        "status": "queued",
                        "document_source": "https://example.com/sample-report.pdf",
                        "webhook_url": "https://myapp.com/webhooks/doc-ready",
                        "created_at": "2026-03-29T15:00:00Z",
                        "updated_at": "2026-03-29T15:00:00Z",
                        "result": None
                    }
                },
                "file_upload": {
                    "summary": "Job from file upload",
                    "value": {
                        "_id": "664f1a2b3c4d5e6f7a8b9c0e",
                        "status": "queued",
                        "document_source": "quarterly-report.pdf",
                        "webhook_url": None,
                        "created_at": "2026-03-29T15:00:00Z",
                        "updated_at": "2026-03-29T15:00:00Z",
                        "result": None
                    }
                }
            }
        }
    }
}

_job_list_example = {
    "description": "List of jobs",
    "content": {
        "application/json": {
            "examples": {
                "mixed_jobs": {
                    "summary": "Jobs in various states",
                    "value": [
                        {
                            "_id": "664f1a2b3c4d5e6f7a8b9c0d",
                            "status": "completed",
                            "document_source": "https://example.com/sample-report.pdf",
                            "webhook_url": "https://myapp.com/webhooks/doc-ready",
                            "created_at": "2026-03-29T15:00:00Z",
                            "updated_at": "2026-03-29T15:05:00Z",
                            "result": {"pages": 5, "text": "Extracted content..."}
                        },
                        {
                            "_id": "664f1a2b3c4d5e6f7a8b9c0e",
                            "status": "queued",
                            "document_source": "quarterly-report.pdf",
                            "webhook_url": None,
                            "created_at": "2026-03-29T15:10:00Z",
                            "updated_at": "2026-03-29T15:10:00Z",
                            "result": None
                        }
                    ]
                }
            }
        }
    }
}

_job_detail_example = {
    "description": "Single job details",
    "content": {
        "application/json": {
            "examples": {
                "completed_job": {
                    "summary": "A completed job with results",
                    "value": {
                        "_id": "664f1a2b3c4d5e6f7a8b9c0d",
                        "status": "completed",
                        "document_source": "https://example.com/sample-report.pdf",
                        "webhook_url": "https://myapp.com/webhooks/doc-ready",
                        "created_at": "2026-03-29T15:00:00Z",
                        "updated_at": "2026-03-29T15:05:00Z",
                        "result": {"pages": 5, "text": "Extracted document content..."}
                    }
                },
                "queued_job": {
                    "summary": "A job still in queue",
                    "value": {
                        "_id": "664f1a2b3c4d5e6f7a8b9c0e",
                        "status": "queued",
                        "document_source": "quarterly-report.pdf",
                        "webhook_url": None,
                        "created_at": "2026-03-29T15:10:00Z",
                        "updated_at": "2026-03-29T15:10:00Z",
                        "result": None
                    }
                }
            }
        }
    }
}


# ── Routes ──────────────────────────────────────────────────────────────────

@router.post(
    "/jobs",
    response_model=Job,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limiter)],
    summary="Submit a document for processing",
    responses={
        201: _job_created_example,
        400: {
            "description": "Invalid submission",
            "content": {
                "application/json": {
                    "example": {"detail": "Job creation failed."}
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded. Max 10 requests per second."}
                }
            }
        }
    }
)
async def create_job(
    job_create: JobCreate,
    service: JobService = Depends(get_job_service)
):
    """
    **Submit a document for asynchronous processing via JSON.**

    Provide a `document_source` (URL or filename) and an optional `webhook_url`.

    **Quick test (Swagger):**
    1. Click **"Try it out"**. The JSON body is **automatically pre-filled**.
    2. Click **"Execute"**. 
    3. Copy the `_id` from the response to track status.
    """
    return await service.create_job(job_create)


@router.get(
    "/jobs",
    response_model=List[Job],
    dependencies=[Depends(rate_limiter)],
    summary="List all processing jobs",
    responses={
        200: _job_list_example,
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded. Max 10 requests per second."}
                }
            }
        }
    }
)
async def list_jobs(
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip (for pagination)",
        examples=[0]
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of records to return",
        examples=[10]
    ),
    service: JobService = Depends(get_job_service)
):
    """
    **Retrieve a paginated list of all jobs.**

    Use `skip` and `limit` to paginate through results.

    **Quick test (Swagger):**
    1. Leave defaults (skip=0, limit=10) or adjust as needed
    2. Click **Execute** to see all submitted jobs
    """
    return await service.list_jobs(skip, limit)


@router.get(
    "/jobs/{job_id}",
    response_model=Job,
    dependencies=[Depends(rate_limiter)],
    summary="Get a specific job by ID",
    responses={
        200: _job_detail_example,
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Job 664f1a2b3c4d5e6f7a8b9c0d not found."}
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded. Max 10 requests per second."}
                }
            }
        }
    }
)
async def get_job(
    job_id: str = Path(
        ...,
        description="The unique ID of the job (returned from POST /jobs)",
        examples=["664f1a2b3c4d5e6f7a8b9c0d"]
    ),
    service: JobService = Depends(get_job_service)
):
    """
    **Retrieve the status and result of a specific job.**

    **Quick test (Swagger):**
    1. Paste the `_id` value you received from the POST /jobs response
    2. Click **Execute** to see the current status
    """
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found."
        )
    return job
