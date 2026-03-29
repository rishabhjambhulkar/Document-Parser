from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.job import Job, JobStatus, JobCreate
from app.db.mongodb import get_database
from typing import List, Optional
from datetime import datetime
import uuid

class JobRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_job(self, job_create: JobCreate) -> Job:
        job_id = str(uuid.uuid4())
        job_document = {
            "_id": job_id,
            "status": JobStatus.QUEUED,
            "document_source": job_create.document_source,
            "webhook_url": job_create.webhook_url,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "result": None
        }
        await self.collection.insert_one(job_document)
        return Job(**job_document)

    async def get_job(self, job_id: str) -> Optional[Job]:
        job_document = await self.collection.find_one({"_id": job_id})
        if job_document:
            return Job(**job_document)
        return None

    async def update_job(self, job_id: str, update_data: dict) -> Optional[Job]:
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": job_id},
            {"$set": update_data}
        )
        return await self.get_job(job_id)

    async def list_jobs(self, skip: int = 0, limit: int = 10) -> List[Job]:
        cursor = self.collection.find().skip(skip).limit(limit)
        jobs = []
        async for doc in cursor:
            jobs.append(Job(**doc))
        return jobs

async def get_job_repository():
    db = await get_database()
    return JobRepository(db["jobs"])
