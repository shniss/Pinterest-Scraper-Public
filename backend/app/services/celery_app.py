"""
Celery Application

This module initializes the Celery application with the following configuration:
- Task serialization format
- Timezone
- Task discovery
"""

from celery import Celery
from app.util.config import get_settings

s = get_settings()
celery_app = Celery("pinmatch", broker=s.redis_url, backend=s.redis_url)

# celery config
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# discover tasks in the app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])
