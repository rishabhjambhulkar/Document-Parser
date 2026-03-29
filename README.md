# Asynchronous Document Processing API System

This system provides a backend for asynchronous document processing with job tracking, background workers, and rate limiting.

## Features
- **FastAPI Backend**: High-performance API for job submission and status tracking.
- **JSON Job Submission**: Simplified job creation with pre-filled examples in Swagger.
- **Celery + Redis**: Background processing queue for document parsing simulations.
- **MongoDB**: Persistent storage for job states and results.
- **Rate Limiting**: Custom Redis-based rate limiter (10 requests per second per IP).
- **SOLID Design**: Repository and Service patterns for clean separation of concerns.

## Prerequisites
- Docker & Docker Compose

## Quick Start (Docker)
1. **Build and start all services**:
   ```bash
   docker-compose up --build -d
   ```
2. **Access the Services**:
   - **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/](http://localhost:8000/)

## How to Test via Swagger UI

1. Open [**http://localhost:8000/docs**](http://localhost:8000/docs).
2. Expand the **`POST /api/v1/jobs`** endpoint.
3. Click **"Try it out"**. The JSON body is **automatically pre-filled** with a sample URL and webhook.
4. Click **"Execute"**. You will receive a `201 Created` response with a job `_id`.
5. Scroll down to **`GET /api/v1/jobs/{job_id}`**, paste the `_id`, and see the status!

## Running Tests

### 1. Run Standard Unit Tests
To run the basic API and worker tests:
```bash
docker-compose exec api pytest tests/test_api.py tests/test_worker.py
```

### 2. Run Load Test (Verify 10 req/sec limit)
To verify the rate limiter blocks more than 10 requests in a single second:
```bash
docker-compose exec api pytest tests/test_load.py
```

## Architecture Design

The system follows a decoupled, asynchronous architecture to ensure high performance and reliability.

```mermaid
graph TD
    User((User)) -->|POST /jobs| API[FastAPI API]
    User -->|GET /jobs/{id}| API
    API -->|Incr/Exp| RedisRL[(Redis - Rate Limit)]
    API -->|Store Initial Job| MongoDB[(MongoDB - Persistence)]
    API -->|Dispatch Task| RedisBroker[(Redis - Message Broker)]
    RedisBroker -->|Consume Task| Worker[Celery Worker]
    Worker -->|Simulate Process| Worker
    Worker -->|Update Status/Results| MongoDB
    Worker -->|Optional Callback| Webhook((External Webhook))
```

### Component Breakdown
1.  **FastAPI API**: Asynchronous entry point. Validates requests, enforces rate limits via Redis, and offloads heavy processing to Celery.
2.  **Redis (Broker & Rate Limiter)**: Acts as the high-speed communication channel between the API and workers. Also stores rolling-window rate limit counters.
3.  **Celery Workers**: Independent processes that consume jobs from Redis and perform the actual document processing simulation.
4.  **MongoDB**: The source of truth for all job data, allowing the API to provide instant status updates while jobs are still being processed.

## Low-Level Design (LLD)

The codebase implements several design patterns to maintain clean, testable code:

-   **Repository Pattern (`app/db/repository.py`)**: Abstracting MongoDB operations ensures the business logic doesn't depend on specific database drivers. It handles the `_id` to `id` mapping and Pydantic model conversion.
-   **Service Pattern (`app/services/job_service.py`)**: The central "brain" that coordinates between the Repository and the task queue. It ensures atomic-like operations (saving to DB before dispatching to Celery).
-   **Dependency Injection**: Used extensively in FastAPI routes (e.g., `get_job_service`, `get_redis`) to make components interchangeable and easily mockable for unit tests.
-   **Pydantic Models (`app/models/job.py`)**: Dual-purpose models used for both API request/response validation and database schema definition, ensuring type safety across the entire stack.

## Scalability

This architecture is designed to scale horizontally across every tier:

1.  **API Scaling**: Since the FastAPI processes are stateless, you can launch multiple API containers behind a Load Balancer (Nginx/HAProxy) to handle millions of requests.
2.  **Worker Scaling**: The system's primary bottleneck is the "processing" time. You can scale the Celery Worker tier independently by adding more containers or server nodes without affecting the API's responsiveness.
3.  **Broker Efficiency**: Redis handles thousands of messages per second with minimal latency, ensuring the "handover" from API to Worker is nearly instantaneous.
4.  **Database Scaling**: MongoDB can be scaled through **Sharding** (distributing data across machines) and **Replica Sets** (ensuring high availability and read-scalability).
5.  **Distributed Rate Limiting**: Unlike memory-based limiters, using Redis ensures that rate limits are consistently enforced even if a user's requests are spread across different API nodes.
