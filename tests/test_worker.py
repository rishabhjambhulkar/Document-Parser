import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.worker.tasks import run_process_task
from app.models.job import JobStatus
import asyncio

@pytest.mark.asyncio
@patch("app.worker.tasks.update_job_in_db", new_callable=AsyncMock)
@patch("app.worker.tasks.send_webhook", new_callable=AsyncMock)
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_run_process_task_success(mock_sleep, mock_webhook, mock_update):
    # Setup
    job_id = "test-job-id"
    source = "doc.pdf"
    webhook_url = "http://webhook.com"
    
    # Execute
    # Since run_process_task uses random.random() for success/failure,
    # we can patch random too, or just test that it calls update_job_in_db at least twice
    with patch("random.random", return_value=0.1): # Success
        await run_process_task(job_id, source, webhook_url)
    
    # Assertions
    # First call to PROCESSING
    mock_update.assert_any_call(job_id, {"status": JobStatus.PROCESSING})
    
    # Second call to COMPLETED (since we mocked random.random to 0.1 < 0.9)
    # Check that it's called with status COMPLETED
    completed_call_args = [call.args for call in mock_update.call_args_list if call.args[1].get("status") == JobStatus.COMPLETED]
    assert len(completed_call_args) == 1
    
    # Check webhook call
    mock_webhook.assert_called_once()
    assert mock_webhook.call_args.args[0] == webhook_url
    assert mock_webhook.call_args.args[1]["status"] == JobStatus.COMPLETED

@pytest.mark.asyncio
@patch("app.worker.tasks.update_job_in_db", new_callable=AsyncMock)
@patch("app.worker.tasks.send_webhook", new_callable=AsyncMock)
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_run_process_task_failure(mock_sleep, mock_webhook, mock_update):
    # Setup
    job_id = "fail-job-id"
    source = "bad.pdf"
    webhook_url = None
    
    # Execute
    # Patch random.random to return 1.0 (>= 0.9) so it fails
    with patch("random.random", return_value=1.0):
        await run_process_task(job_id, source, webhook_url)
    
    # Assertions
    # Final status should be FAILED
    failed_call_args = [call.args for call in mock_update.call_args_list if call.args[1].get("status") == JobStatus.FAILED]
    assert len(failed_call_args) == 1
    
    # Webhook should not be sent if None
    mock_webhook.assert_called_once_with(None, mock_webhook.call_args.args[1])
