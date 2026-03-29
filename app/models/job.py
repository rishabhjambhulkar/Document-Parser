from enum import Enum
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobUpdate(BaseModel):
    status: JobStatus
    result: Optional[Any] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "completed",
                    "result": {"pages": 5, "text": "Extracted document content..."},
                    "updated_at": "2026-03-29T15:30:00Z"
                }
            ]
        }
    }

class JobCreate(BaseModel):
    document_source: str = Field(
        ...,
        description="URL of the document or uploaded filename",
        examples=["https://example.com/sample-report.pdf"]
    )
    webhook_url: Optional[str] = Field(
        None,
        description="Optional URL to receive a callback when processing completes",
        examples=["https://myapp.com/webhooks/doc-ready"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_source": "https://example.com/sample-report.pdf",
                    "webhook_url": "https://myapp.com/webhooks/doc-ready"
                },
                {
                    "document_source": "quarterly-report.pdf",
                    "webhook_url": None
                }
            ]
        }
    }

class Job(BaseModel):
    id: str = Field(..., alias="_id", examples=["664f1a2b3c4d5e6f7a8b9c0d"])
    status: JobStatus = Field(JobStatus.QUEUED, examples=["queued"])
    document_source: str = Field(..., examples=["https://example.com/sample-report.pdf"])
    webhook_url: Optional[str] = Field(None, examples=["https://myapp.com/webhooks/doc-ready"])
    created_at: datetime = Field(default_factory=datetime.utcnow, examples=["2026-03-29T15:00:00Z"])
    updated_at: datetime = Field(default_factory=datetime.utcnow, examples=["2026-03-29T15:00:05Z"])
    result: Optional[Any] = Field(None, examples=[{"pages": 5, "text": "Extracted document content..."}])

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        },
        "json_schema_extra": {
            "examples": [
                {
                    "_id": "664f1a2b3c4d5e6f7a8b9c0d",
                    "status": "queued",
                    "document_source": "https://example.com/sample-report.pdf",
                    "webhook_url": "https://myapp.com/webhooks/doc-ready",
                    "created_at": "2026-03-29T15:00:00Z",
                    "updated_at": "2026-03-29T15:00:00Z",
                    "result": None
                },
                {
                    "_id": "664f1a2b3c4d5e6f7a8b9c0e",
                    "status": "completed",
                    "document_source": "quarterly-report.pdf",
                    "webhook_url": None,
                    "created_at": "2026-03-29T15:00:00Z",
                    "updated_at": "2026-03-29T15:05:00Z",
                    "result": {"pages": 5, "text": "Extracted document content..."}
                }
            ]
        }
    }
