from app.db.repository import JobRepository
from app.models.job import Job, JobCreate, JobStatus
from app.core.celery_app import celery_app
from typing import Optional, List

class JobService:
    def __init__(self, repository: JobRepository):
        self.repository = repository

    async def create_job(self, job_create: JobCreate) -> Job:
        # Create job in database
        job = await self.repository.create_job(job_create)
        
        # Dispatch to Celery worker
        # task.delay() is the standard way to enqueue a job
        celery_app.send_task(
            "app.worker.tasks.process_document_job",
            args=[job.id, job.document_source, job.webhook_url],
            queue="document_tasks"
        )
        
        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        return await self.repository.get_job(job_id)

    async def list_jobs(self, skip: int = 0, limit: int = 10) -> List[Job]:
        return await self.repository.list_jobs(skip, limit)
