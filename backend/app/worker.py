"""Background worker for PDF text extraction using APScheduler.

Implements adaptive polling: actively polls when there's work,
pauses after consecutive idle checks, resumes when new uploads arrive.
"""

import logging
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExtractionWorkerManager:
    """Manages the extraction worker with adaptive polling.

    The worker actively polls when there's work to do, but pauses
    after a configurable number of consecutive idle checks.
    When new uploads arrive, the worker is signaled to resume.
    """

    def __init__(self, interval_seconds: int = 5, max_idle_checks: int = 10):
        self.interval_seconds = interval_seconds
        self.max_idle_checks = max_idle_checks
        self.idle_count = 0
        self.scheduler = None
        self.app = None
        self._lock = threading.Lock()
        self._is_running = False

    def init_app(self, app):
        """Initialize with Flask application.

        Args:
            app: Flask application instance
        """
        self.app = app
        self.scheduler = BackgroundScheduler()
        logger.info(
            f"Extraction worker initialized "
            f"(interval: {self.interval_seconds}s, "
            f"max idle: {self.max_idle_checks})"
        )

    def _process_queue(self):
        """Process the extraction queue with idle tracking."""
        if not self.app:
            return

        with self.app.app_context():
            from app.services.extraction_service import ExtractionService
            from app.models.extraction_queue import ExtractionQueue

            pending_count = ExtractionQueue.query.filter_by(status="pending").count()

            if pending_count > 0:
                # Reset idle count when there's work
                self.idle_count = 0
                logger.info(
                    f"Processing extraction queue. {pending_count} items pending."
                )

                success, error = ExtractionService.process_next()

                if success:
                    logger.info("Successfully processed one extraction item.")
                elif error:
                    logger.warning(f"Extraction failed: {error}")
            else:
                # Increment idle count
                self.idle_count += 1
                logger.debug(
                    f"Queue empty. Idle count: {self.idle_count}/{self.max_idle_checks}"
                )

                if self.idle_count >= self.max_idle_checks:
                    logger.info(
                        f"No work for {self.max_idle_checks} checks. "
                        "Pausing worker until next upload."
                    )
                    self._pause()

    def start(self):
        """Start the worker scheduler."""
        with self._lock:
            if self._is_running:
                return

            self.idle_count = 0

            if not self.scheduler.running:
                self.scheduler.start()

            # Add or replace the job
            try:
                self.scheduler.add_job(
                    func=self._process_queue,
                    trigger=IntervalTrigger(seconds=self.interval_seconds),
                    id="extraction_worker",
                    name="PDF Extraction Worker",
                    replace_existing=True,
                )
            except Exception:
                # Job might already exist, reschedule it
                self.scheduler.reschedule_job(
                    "extraction_worker",
                    trigger=IntervalTrigger(seconds=self.interval_seconds),
                )

            self._is_running = True
            logger.info("Extraction worker started.")

    def _pause(self):
        """Pause the worker (internal method)."""
        with self._lock:
            if not self._is_running:
                return

            try:
                self.scheduler.pause_job("extraction_worker")
            except Exception:
                pass

            self._is_running = False
            logger.info("Extraction worker paused.")

    def wake_up(self):
        """Signal the worker to resume processing.

        Call this when new documents are uploaded.
        """
        with self._lock:
            if self._is_running:
                # Already running, just reset idle count
                self.idle_count = 0
                return

            self.idle_count = 0

            try:
                self.scheduler.resume_job("extraction_worker")
                self._is_running = True
                logger.info("Extraction worker resumed.")
            except Exception:
                # Job might not exist, start fresh
                self.start()

    def shutdown(self):
        """Shutdown the worker scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Extraction worker shut down.")

    @property
    def is_running(self):
        """Check if the worker is currently active."""
        return self._is_running


# Global worker instance
extraction_worker = ExtractionWorkerManager()


def init_worker(app, interval_seconds: int = 5, max_idle_checks: int = 10):
    """Initialize and start the extraction worker.

    Args:
        app: Flask application instance
        interval_seconds: Polling interval in seconds
        max_idle_checks: Number of idle checks before pausing
    """
    extraction_worker.interval_seconds = interval_seconds
    extraction_worker.max_idle_checks = max_idle_checks
    extraction_worker.init_app(app)
    extraction_worker.start()


def run_worker():
    """Run the extraction worker as a standalone process."""
    import os
    import time
    from app import create_app

    config_name = os.environ.get("FLASK_CONFIG", "development")
    app = create_app(config_name)

    logger.info("Starting PDF extraction worker (standalone mode)...")

    init_worker(app)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down extraction worker...")
        extraction_worker.shutdown()


if __name__ == "__main__":
    run_worker()
