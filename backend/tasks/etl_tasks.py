"""
Celery ETL tasks for syncing clinical trials from ClinicalTrials.gov.
"""
import logging
import asyncio
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from backend.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "clinicalmind",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-trials-every-6-hours": {
            "task": "backend.tasks.etl_tasks.sync_trials_task",
            "schedule": crontab(minute=0, hour="*/6"),
        },
    },
)


def _run_sync_in_loop(coro):
    """Helper to run an async coroutine from sync Celery context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _async_sync_trials(max_pages: int = 5):
    """Async implementation of trial sync."""
    from backend.database import AsyncSessionLocal
    from backend.services.trial_fetcher import fetch_recruiting_trials
    from backend.services.embedder import embed_text, build_trial_text
    from backend.models.trial import Trial
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    stats = {"new": 0, "updated": 0, "errors": 0}
    trials_data = fetch_recruiting_trials(page_size=100, max_pages=max_pages)
    logger.info(f"[ETL] Fetched {len(trials_data)} trials from ClinicalTrials.gov")

    async with AsyncSessionLocal() as session:
        for trial_dict in trials_data:
            try:
                text_for_embed = build_trial_text(trial_dict)
                embedding = embed_text(text_for_embed)

                # Check if trial exists
                result = await session.execute(
                    select(Trial).where(Trial.nct_id == trial_dict["nct_id"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.title = trial_dict["title"]
                    existing.status = trial_dict["status"]
                    existing.phase = trial_dict["phase"]
                    existing.conditions = trial_dict["conditions"]
                    existing.interventions = trial_dict["interventions"]
                    existing.eligibility_criteria = trial_dict["eligibility_criteria"]
                    existing.summary = trial_dict["summary"]
                    existing.embedding = embedding
                    existing.last_synced = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    trial = Trial(
                        nct_id=trial_dict["nct_id"],
                        title=trial_dict["title"],
                        status=trial_dict["status"],
                        phase=trial_dict["phase"],
                        conditions=trial_dict["conditions"],
                        interventions=trial_dict["interventions"],
                        eligibility_criteria=trial_dict["eligibility_criteria"],
                        summary=trial_dict["summary"],
                        embedding=embedding,
                        last_synced=datetime.utcnow(),
                    )
                    session.add(trial)
                    stats["new"] += 1
            except Exception as e:
                logger.error(f"[ETL] Error processing trial {trial_dict.get('nct_id')}: {e}")
                stats["errors"] += 1

        await session.commit()

    logger.info(
        f"[ETL] Sync complete. New: {stats['new']}, Updated: {stats['updated']}, Errors: {stats['errors']}"
    )
    return stats


async def _async_reindex_all():
    """Async implementation of full reindex."""
    from backend.database import AsyncSessionLocal
    from backend.models.trial import Trial
    from backend.services.embedder import embed_text, build_trial_text
    from sqlalchemy import select

    stats = {"reindexed": 0, "errors": 0}

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Trial))
        trials = result.scalars().all()
        for trial in trials:
            try:
                trial_dict = {
                    "title": trial.title,
                    "conditions": trial.conditions or [],
                    "eligibility_criteria": trial.eligibility_criteria,
                    "summary": trial.summary,
                }
                text = build_trial_text(trial_dict)
                trial.embedding = embed_text(text)
                stats["reindexed"] += 1
            except Exception as e:
                logger.error(f"[Reindex] Error on {trial.nct_id}: {e}")
                stats["errors"] += 1

        await session.commit()

    logger.info(f"[Reindex] Complete. Reindexed: {stats['reindexed']}, Errors: {stats['errors']}")
    return stats


@celery_app.task(name="backend.tasks.etl_tasks.sync_trials_task", bind=True)
def sync_trials_task(self, max_pages: int = 5):
    """Celery task: fetch and upsert recruiting trials from ClinicalTrials.gov."""
    logger.info("[ETL] Starting sync_trials_task")
    try:
        stats = _run_sync_in_loop(_async_sync_trials(max_pages=max_pages))
        return stats
    except Exception as exc:
        logger.error(f"[ETL] sync_trials_task failed: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(name="backend.tasks.etl_tasks.reindex_all_trials_task", bind=True)
def reindex_all_trials_task(self):
    """Celery task: re-embed all trials in the database."""
    logger.info("[Reindex] Starting reindex_all_trials_task")
    try:
        stats = _run_sync_in_loop(_async_reindex_all())
        return stats
    except Exception as exc:
        logger.error(f"[Reindex] reindex_all_trials_task failed: {exc}")
        raise self.retry(exc=exc, countdown=120, max_retries=2)
