import asyncio
import logging
import signal
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseWorker(ABC):
    """
    Abstract Base class for Distributed Job Scheduler Workers.
    Manages loop state, lifecycle, and graceful termination hooks.
    """

    def __init__(self, worker_id: str, queue_name: str):
        self.worker_id = worker_id
        self.queue_name = queue_name
        self.logger = logging.getLogger(f"app.worker.{self.worker_id}")
        self._running = False
        self._current_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the worker loop."""
        self._running = True
        self.logger.info(f"Worker {self.worker_id} starting on queue '{self.queue_name}'...")
        
        # Register signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
            except NotImplementedError:
                # Signal handlers are not fully supported on Windows in asyncio
                pass

        try:
            await self._run_loop()
        except asyncio.CancelledError:
            self.logger.info("Worker run loop cancelled.")
        except Exception as e:
            self.logger.exception(f"Fatal error encountered in worker loop: {str(e)}")
        finally:
            await self.cleanup()

    async def _run_loop(self) -> None:
        """Worker loop that pulls and executes jobs."""
        while self._running:
            try:
                # 1. Fetch next job from queue (abstracted)
                job = await self._fetch_next_job()
                if not job:
                    # No job in queue, sleep briefly (avoid busy wait)
                    await asyncio.sleep(1.0)
                    continue

                # 2. Process the job
                self.logger.debug(f"Job found: {job.get('id')}. Processing...")
                await self._process_job(job)

            except Exception as e:
                self.logger.error(f"Error in execution cycle: {str(e)}")
                await asyncio.sleep(2.0)

    async def shutdown(self) -> None:
        """Triggers graceful shutdown of the worker loop and currently active tasks."""
        self.logger.info("Shutdown signal received. Stopping worker...")
        self._running = False
        if self._current_task and not self._current_task.done():
            self.logger.info("Cancelling active job task...")
            self._current_task.cancel()

    @abstractmethod
    async def _fetch_next_job(self) -> Optional[Dict[str, Any]]:
        """Fetch next pending job. Implement in concrete subclasses (e.g., Redis / DB)."""
        pass

    @abstractmethod
    async def _process_job(self, job: Dict[str, Any]) -> None:
        """Execute task logic. Implement in concrete subclasses."""
        pass

    async def cleanup(self) -> None:
        """Lifecycle hook to clean up resources (DB connections, sockets, etc.) on shutdown."""
        self.logger.info(f"Worker {self.worker_id} cleanup complete.")
