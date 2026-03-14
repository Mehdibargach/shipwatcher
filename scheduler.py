"""
Scheduler — runs checks automatically at regular intervals.
Uses APScheduler to run checks in the background.
"""

import os
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import store
import checker
import alerts

logger = logging.getLogger("shipwatcher.scheduler")

scheduler = AsyncIOScheduler()

CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "6"))


async def scheduled_check():
    """Run all checks and send alerts if any fail."""
    logger.info("Scheduled check starting...")
    projects = store.list_projects()
    if not projects:
        logger.info("No projects to check")
        return

    all_results = await checker.check_all_projects(projects)

    # Update last_check for all projects
    now = datetime.now(timezone.utc).isoformat()
    for p in projects:
        store.update_project(p["id"], {"last_check": now})

    # Find failures
    failures = [r for r in all_results if not r.success]
    passed = len(all_results) - len(failures)

    logger.info(f"Check complete: {passed}/{len(all_results)} passed")

    if failures:
        logger.warning(f"{len(failures)} check(s) failed — sending alert")
        await alerts.send_alert(failures, total=len(all_results))
    else:
        logger.info("All checks passed — no alert needed")


def start_scheduler():
    """Start the background scheduler."""
    if CHECK_INTERVAL_HOURS <= 0:
        logger.info("Scheduler disabled (CHECK_INTERVAL_HOURS=0)")
        return

    scheduler.add_job(
        scheduled_check,
        trigger=IntervalTrigger(hours=CHECK_INTERVAL_HOURS),
        id="scheduled_check",
        name=f"Check all projects every {CHECK_INTERVAL_HOURS}h",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — checks every {CHECK_INTERVAL_HOURS}h")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
