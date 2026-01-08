"""Flask CLI commands for the application."""

import click
from flask import current_app
from flask.cli import with_appcontext


@click.command("run-worker")
@click.option("--interval", default=5, help="Queue check interval in seconds")
@with_appcontext
def run_worker_command(interval):
    """Run the PDF extraction worker."""
    import time

    from app.worker import create_scheduler

    click.echo(f"Starting PDF extraction worker (interval: {interval}s)...")

    scheduler = create_scheduler(current_app._get_current_object(), interval)
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        click.echo("\nShutting down extraction worker...")
        scheduler.shutdown()


@click.command("process-queue")
@click.option("--all", "process_all", is_flag=True, help="Process all pending items")
@with_appcontext
def process_queue_command(process_all):
    """Process pending items in the extraction queue."""
    from app.services.extraction_service import ExtractionService
    from app.models.extraction_queue import ExtractionQueue

    pending_count = ExtractionQueue.query.filter_by(status="pending").count()

    if pending_count == 0:
        click.echo("No pending items in the queue.")
        return

    click.echo(f"Found {pending_count} pending items.")

    if process_all:
        processed = 0
        while True:
            success, error = ExtractionService.process_next()
            if error:
                click.echo(f"Error: {error}")
            if not ExtractionQueue.query.filter_by(status="pending").first():
                break
            processed += 1
        click.echo(f"Processed {processed} items.")
    else:
        success, error = ExtractionService.process_next()
        if success:
            click.echo("Successfully processed one item.")
        elif error:
            click.echo(f"Error: {error}")


@click.command("queue-status")
@with_appcontext
def queue_status_command():
    """Show extraction queue status."""
    from app.models.extraction_queue import ExtractionQueue

    pending = ExtractionQueue.query.filter_by(status="pending").count()
    processing = ExtractionQueue.query.filter_by(status="processing").count()
    completed = ExtractionQueue.query.filter_by(status="completed").count()
    failed = ExtractionQueue.query.filter_by(status="failed").count()

    click.echo("Extraction Queue Status:")
    click.echo(f"  Pending:    {pending}")
    click.echo(f"  Processing: {processing}")
    click.echo(f"  Completed:  {completed}")
    click.echo(f"  Failed:     {failed}")


def register_cli(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(run_worker_command)
    app.cli.add_command(process_queue_command)
    app.cli.add_command(queue_status_command)
