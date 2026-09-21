import asyncio
import logging

logger = logging.getLogger("app.tasks.communication")

async def dispatch_email(payload: dict) -> dict:
    """Mock email dispatch task."""
    recipient = payload.get("recipient", "user@acme.com")
    logger.info(f"Dispatching campaign email to {recipient}...")
    await asyncio.sleep(2.0)
    return {"status": "email_sent", "recipient": recipient}
