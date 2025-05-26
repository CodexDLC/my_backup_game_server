






import asyncio
import os

from sqlalchemy import func, select
from game_server.Logic.DataAccessLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_coordinator_listener import REDIS_CHANNELS
from game_server.app_cache.redis_client import RedisClient
from game_server.database.models.models import AutoSessions 


class AutoSessionWatcher:
    def __init__(self):
        self.db = AsyncSessionLocal
        self.redis = RedisClient()
        self._active = False
        self._task = None
        logger.info("🔧 AutoSessionWatcher инициализирован.")

    async def periodic_check(self,):
        """Фоновая проверка auto_sessions"""
        while self._active:
            try:
                logger.debug("🔄 Запуск проверки задач...")
                if await self._has_pending_tasks():
                    logger.info("🔥 Обнаружены задачи, отправка `run_collector` в Redis...")
                    await self.redis.publish(REDIS_CHANNELS["coordinator"], "run_collector")
                    logger.info("✅ Команда `run_collector` отправлена!")
                else:
                    logger.debug("⚡ Нет задач для обработки.")

            except Exception as e:
                logger.error("❌ Ошибка в Watcher:", exc_info=True)

            logger.debug("⏳ Ожидание 30 секунд перед следующей проверкой...")
            await asyncio.sleep(30)  # 🔄 Проверка каждые 30 секунд

    async def start(self):
        """Запускает фоновую проверку"""
        if self._task and not self._task.done():
            logger.warning("⚠️ Watcher уже работает, перезапуск не требуется")
            return
              
        self._active = True  # ✅ Активируем процесс
        logger.info("🚀 Запуск фонового процесса AutoSessionWatcher...")
        self._task = asyncio.create_task(self.periodic_check())  # ✅ Запускаем в фоне
        logger.info("✅ AutoSessionWatcher запущен!")

    async def stop(self):
        """Останавливает watcher"""
        logger.warning("⚠️ Остановка AutoSessionWatcher...")
        self._active = False
        if self._task:
            self._task.cancel()  # ❌ Завершаем фоновую задачу
            logger.info("✅ Фоновая задача остановлена!")
        logger.info("❌ AutoSessionWatcher полностью остановлен.")

    async def _has_pending_tasks(self) -> bool:
        logger.debug("📡 Проверка наличия задач в авто-сессиях через SQLAlchemy...")
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AutoSessions).where(AutoSessions.next_tick_at <= func.now())
            )
            records = result.scalars().all()
        logger.info(f"🔍 Результат проверки: {records}")
        return bool(records)
