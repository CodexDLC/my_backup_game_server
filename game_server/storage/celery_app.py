from celery import Celery
from game_server.config.redis_config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery("game_server")

celery_app.config_from_object({
    'broker_url': CELERY_BROKER_URL,
    'result_backend': CELERY_RESULT_BACKEND,
})

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'process-global-tick': {
        'task': 'game_server.tasks.process_global_tick',
        'schedule': crontab(minute='*/1'),
    },
}
