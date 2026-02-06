"""Background worker for typo check processing using APScheduler.

Implements adaptive polling: actively polls when there's work,
pauses after consecutive idle checks, resumes when new jobs arrive.
"""

import logging
import threading
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class TypoCheckWorkerManager:
    """Manages the typo check worker with adaptive polling."""

    def __init__(self, interval_seconds: int = 3, max_idle_checks: int = 10):
        self.interval_seconds = interval_seconds
        self.max_idle_checks = max_idle_checks
        self.idle_count = 0
        self.scheduler = None
        self.app = None
        self._lock = threading.Lock()
        self._is_running = False

    def init_app(self, app):
        """Initialize with Flask application."""
        self.app = app
        self.scheduler = BackgroundScheduler()
        logger.info(
            f"Typo check worker initialized "
            f"(interval: {self.interval_seconds}s, "
            f"max idle: {self.max_idle_checks})"
        )

    def _cleanup_stale_jobs(self):
        """Mark jobs stuck in processing for over 1 hour as failed."""
        from app.models.typo_check_job import TypoCheckJob
        from app import db

        stale_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        stale_jobs = TypoCheckJob.query.filter(
            TypoCheckJob.status == "processing",
            TypoCheckJob.started_at < stale_cutoff,
        ).all()

        for job in stale_jobs:
            job.status = "failed"
            job.error_message = "Job timed out (stale processing)"
            job.completed_at = datetime.now(timezone.utc)
            logger.warning(f"Marked stale typo check job {job.id} as failed")

        if stale_jobs:
            db.session.commit()

    def _process_queue(self):
        """Process the typo check queue with idle tracking."""
        if not self.app:
            return

        with self.app.app_context():
            from app.models.typo_check_job import TypoCheckJob
            from app.services.typo_checker_service import TypoCheckerService

            self._cleanup_stale_jobs()

            job = (
                TypoCheckJob.query.filter_by(status="pending")
                .order_by(TypoCheckJob.created_at.asc())
                .first()
            )

            if job:
                self.idle_count = 0
                logger.info(f"Processing typo check job {job.id}")
                TypoCheckerService.process_job(job.id)
            else:
                self.idle_count += 1
                if self.idle_count >= self.max_idle_checks:
                    self._pause()

    def start(self):
        """Start the worker scheduler."""
        with self._lock:
            if self._is_running:
                return

            self.idle_count = 0

            if not self.scheduler.running:
                self.scheduler.start()

            try:
                self.scheduler.add_job(
                    func=self._process_queue,
                    trigger=IntervalTrigger(seconds=self.interval_seconds),
                    id="typo_check_worker",
                    name="Typo Check Worker",
                    replace_existing=True,
                )
            except Exception:
                self.scheduler.reschedule_job(
                    "typo_check_worker",
                    trigger=IntervalTrigger(seconds=self.interval_seconds),
                )

            self._is_running = True
            logger.info("Typo check worker started.")

    def _pause(self):
        """Pause the worker."""
        with self._lock:
            if not self._is_running:
                return

            try:
                self.scheduler.pause_job("typo_check_worker")
            except Exception:
                pass

            self._is_running = False
            logger.info("Typo check worker paused.")

    def wake_up(self):
        """Signal the worker to resume processing."""
        with self._lock:
            if self._is_running:
                self.idle_count = 0
                return

            self.idle_count = 0

            try:
                self.scheduler.resume_job("typo_check_worker")
                self._is_running = True
                logger.info("Typo check worker resumed.")
            except Exception:
                self.start()

    def shutdown(self):
        """Shutdown the worker scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Typo check worker shut down.")

    @property
    def is_running(self):
        """Check if the worker is currently active."""
        return self._is_running


typo_check_worker = TypoCheckWorkerManager()


def init_typo_worker(app, interval_seconds: int = 3, max_idle_checks: int = 10):
    """Initialize and start the typo check worker."""
    typo_check_worker.interval_seconds = interval_seconds
    typo_check_worker.max_idle_checks = max_idle_checks
    typo_check_worker.init_app(app)
    typo_check_worker.start()
