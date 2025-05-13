from celery import Celery
from game_server.config.redis_config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Создаем объект Celery
app = Celery("game_server")

# Указываем настройки для брокера и хранилища результатов
app.config_from_object({
    'broker_url': CELERY_BROKER_URL,
    'result_backend': CELERY_RESULT_BACKEND,
})

# Пример задачи
@app.task
def example_task(x, y):
    return x + y


from celery.schedules import crontab

app.conf.beat_schedule = {
    'process-global-tick': {
        'task': 'game_server.tasks.process_global_tick',  # Имя задачи для выполнения
        'schedule': crontab(minute='*/1'),  # Задача будет выполняться каждую минуту
    },
}
