"""Scheduled jobs for environment maintenance."""

from datetime import datetime, timezone

import modal

from modal_executor.app import app
from modal_executor.images import get_base_image
from modal_executor.volume import get_state_volume, MOUNT_PATH, cleanup_stale_files


@app.function(
    schedule=modal.Cron("*/30 * * * *"),  # Every 30 minutes
    retries=3,
    timeout=600,  # 10 minutes max
)
def refresh_environment() -> dict:
    """Periodic refresh of agent execution environment.

    Runs every 30 minutes to:
    1. Warm up the base image (ensures fast cold starts)
    2. Clean up stale cache files
    3. Verify environment is healthy

    Returns:
        Status dict with refresh details
    """
    start_time = datetime.now(timezone.utc)

    # Create a Sandbox to warm up image and clean cache
    sb = modal.Sandbox.create(
        image=get_base_image(),
        volumes={MOUNT_PATH: get_state_volume()},
        timeout=300,  # 5 minutes for cleanup
        app=app,
    )

    try:
        # Verify image is working
        result = sb.exec("python", "--version")
        python_version = result.stdout.read().strip()

        # Clean up stale cache files (older than 7 days)
        files_cleaned = cleanup_stale_files(sb, max_age_days=7)

        # Check disk usage
        du_result = sb.exec("du", "-sh", MOUNT_PATH)
        disk_usage = du_result.stdout.read().strip()

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        return {
            "status": "success",
            "timestamp": end_time.isoformat(),
            "duration_secs": duration,
            "python_version": python_version,
            "files_cleaned": files_cleaned,
            "disk_usage": disk_usage,
        }

    except Exception as e:
        end_time = datetime.now(timezone.utc)
        return {
            "status": "error",
            "timestamp": end_time.isoformat(),
            "duration_secs": (end_time - start_time).total_seconds(),
            "error": str(e),
        }

    finally:
        sb.terminate()


@app.function(timeout=60)
def health_check() -> dict:
    """Quick health check for the executor environment.

    Returns:
        Health status dict
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": "harvest-agent-executor",
    }
