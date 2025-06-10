# game_server/Logic/InfrastructureLogic/celery/task/tasks_watcher.py

from game_server.Logic.InfrastructureLogic.celery.celery_app import app
from game_server.Logic.ApplicationLogic.coordinator_tick.coordinator.tick_AutoSession_Watcher import run_watcher_check
from game_server.services.logging.logging_setup import logger # Используйте ваш Celery логгер

@app.task
async def run_watcher_task():
    """
    Celery-задача, которая запускает цикл проверки сессий Watcher'а.
    """
    logger.info("🚀 Celery: Получена задача на запуск Watcher'а.")
    await run_watcher_check()
    logger.info("🏁 Celery: Задача Watcher'а завершена.")