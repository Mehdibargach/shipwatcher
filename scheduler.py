"""
Scheduler — runs checks automatically at regular intervals.
- Checks every 6h: alert email if failures
- Daily digest at 8am UTC: full summary email
"""

import os
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

import store
import checker
import alerts

logger = logging.getLogger("shipwatcher.scheduler")

scheduler = AsyncIOScheduler()

CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "6"))
DIGEST_HOUR_UTC = int(os.getenv("DIGEST_HOUR_UTC", "8"))


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

    return all_results


async def daily_digest():
    """Run all checks and send daily digest email."""
    logger.info("Daily digest starting...")
    projects = store.list_projects()
    if not projects:
        logger.info("No projects for digest")
        return

    all_results = await checker.check_all_projects(projects)

    # Update last_check
    now = datetime.now(timezone.utc).isoformat()
    for p in projects:
        store.update_project(p["id"], {"last_check": now})

    passed = sum(1 for r in all_results if r.success)
    logger.info(f"Daily digest: {passed}/{len(all_results)} passed — sending digest")

    await alerts.send_daily_digest(all_results)


def start_scheduler():
    """Start the background scheduler."""
    if CHECK_INTERVAL_HOURS > 0:
        scheduler.add_job(
            scheduled_check,
            trigger=IntervalTrigger(hours=CHECK_INTERVAL_HOURS),
            id="scheduled_check",
            name=f"Check all projects every {CHECK_INTERVAL_HOURS}h",
            replace_existing=True,
        )
        logger.info(f"Alert checks: every {CHECK_INTERVAL_HOURS}h")

    scheduler.add_job(
        daily_digest,
        trigger=CronTrigger(hour=DIGEST_HOUR_UTC, minute=0),
        id="daily_digest",
        name=f"Daily digest at {DIGEST_HOUR_UTC}:00 UTC",
        replace_existing=True,
    )
    logger.info(f"Daily digest: every day at {DIGEST_HOUR_UTC}:00 UTC")

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
