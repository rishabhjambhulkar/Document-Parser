from app.core.celery_app import celery_app
from app.db.mongodb import AsyncIOMotorClient
from app.core.config import settings
from app.models.job import JobStatus
import asyncio
import time
import random
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def update_job_in_db(job_id: str, update_data: dict):
    # Short-lived client for worker task
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.APP_DATABASE_NAME]
    collection = db["jobs"]
    update_data["updated_at"] = datetime.utcnow()
    await collection.update_one({"_id": job_id}, {"$set": update_data})
    client.close()

async def send_webhook(webhook_url: str, payload: dict):
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10.0)
            logger.info(f"Webhook sent to {webhook_url}, Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {str(e)}")

async def run_process_task(job_id: str, source: str, webhook_url: str):
    logger.info(f"Starting processing for job {job_id}")
    
    # 1. Update to PROCESSING
    await update_job_in_db(job_id, {"status": JobStatus.PROCESSING})
    
    # 2. Simulate processing (10-20 seconds)
    processing_time = random.uniform(10, 20)
    await asyncio.sleep(processing_time)
    
    # 3. Simulate success or failure
    # Let's say 90% success rate
    success = random.random() < 0.9
    
    if success:
        status = JobStatus.COMPLETED
        result = {
            "document_name": source,
            "page_count": random.randint(1, 50),
            "word_count": random.randint(100, 5000),
            "processed_at": datetime.utcnow().isoformat(),
            "extracted_text_snippet": "This is a mock extracted text result from the document processing system."
        }
    else:
        status = JobStatus.FAILED
        result = {"error": "Internal OCR engine failure simulation."}

    # 4. Update to final status
    await update_job_in_db(job_id, {
        "status": status,
        "result": result
    })
    
    # 5. Send Webhook
    webhook_payload = {
        "job_id": job_id,
        "status": status,
        "result": result
    }
    await send_webhook(webhook_url, webhook_payload)
    
    logger.info(f"Finished job {job_id} with status {status}")

@celery_app.task(name="app.worker.tasks.process_document_job", bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def process_document_job(self, job_id, source, webhook_url):
    # Celery tasks are blocking. We use asyncio.run to bridge to our async logic.
    asyncio.run(run_process_task(job_id, source, webhook_url))
