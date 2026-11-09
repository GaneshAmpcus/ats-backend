from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ats_platform",
    broker=settings.task_broker_url,
    backend=settings.task_result_backend,
)

celery_app.autodiscover_tasks(["app.modules"])

celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.run_celery_tasks_eagerly,
    task_eager_propagates=True,
)
