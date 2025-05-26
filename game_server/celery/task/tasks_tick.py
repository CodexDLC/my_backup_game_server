
# game_server\celery\task\tasks_tick.py

import asyncio
from game_server.celery.celery_app import app

from game_server.services.logging.logging_setup import logger

from game_server.Logic.DomainLogic.tick_infra.collector.tick_collector import schedule_tick


@app.task
def schedule_tick_task():
    """Запускает `schedule_tick()` через Celery."""
    logger.info("🚀 Запуск `schedule_tick()` через Celery Worker")
    try:
        asyncio.run(schedule_tick())  # ✅ Запускаем асинхронную функцию в синхронном контексте
    except Exception as e:
        logger.error(f"❌ Ошибка в `schedule_tick_task()`: {e}")