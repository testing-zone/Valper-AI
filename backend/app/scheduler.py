"""APScheduler jobs, all in local time."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app import briefings
from app.core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)


def start():
    common = {"misfire_grace_time": 900, "coalesce": True, "max_instances": 1}
    scheduler.add_job(briefings.digest, CronTrigger(hour=settings.DIGEST_HOURS, minute=0),
                      id="digest", **common)
    if settings.MORNING_HOUR:
        scheduler.add_job(briefings.morning, CronTrigger(hour=int(settings.MORNING_HOUR), minute=0),
                          id="morning", **common)
        # catch up after sleep: checks every 2 minutes, sends at most once per morning
        scheduler.add_job(briefings.morning_catchup, IntervalTrigger(minutes=2), id="morning_catchup",
                          max_instances=1, coalesce=True)
    if settings.NIGHT_HOUR:
        scheduler.add_job(briefings.night, CronTrigger(hour=int(settings.NIGHT_HOUR), minute=0),
                          id="night", **common)
    scheduler.add_job(briefings.local_news, CronTrigger(hour=settings.LOCAL_NEWS_HOUR, minute=0),
                      id="local", **common)
    if settings.jira_enabled:
        scheduler.add_job(briefings.jira_briefing, CronTrigger(day_of_week="mon-fri", hour=settings.JIRA_HOUR),
                          id="jira", **common)
    from app.tools import orca
    if settings.ORCA_WATCH and orca.available():
        scheduler.add_job(orca.watch, IntervalTrigger(seconds=20), id="orca", max_instances=1, coalesce=True)
    scheduler.add_job(briefings.fire_reminders, IntervalTrigger(seconds=30), id="reminders",
                      max_instances=1, coalesce=True)
    scheduler.start()
    for job in scheduler.get_jobs():
        logger.info(f"Scheduled {job.id}: next run {job.next_run_time}")


def jobs_info() -> list:
    return [{"id": j.id, "next_run": str(j.next_run_time)} for j in scheduler.get_jobs()]


def shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)
