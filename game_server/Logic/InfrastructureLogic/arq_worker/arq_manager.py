# game_server\Logic\InfrastructureLogic\arq\arq_manager.py

from typing import Optional
from arq.connections import RedisSettings, create_pool, ArqRedis


from game_server.config.settings_core import REDIS_CACHE_URL
from game_server.config.logging.logging_setup import app_logger as logger

class ArqPoolManager:
    """
    Класс для управления жизненным циклом ARQ Redis connection pool.
    Предназначен для использования в FastAPI lifespan events.
    """
    def __init__(self):
        self.redis_settings = RedisSettings.from_dsn(REDIS_CACHE_URL)
        self.arq_redis_pool: Optional[ArqRedis] = None
        logger.info("✨ ArqPoolManager инициализирован.")

    async def startup(self):
        """
        Инициализирует пул подключений ARQ Redis.
        """
        logger.info("🔧 Запуск ArqPoolManager: Создание пула подключений Redis для ARQ...")
        try:
            self.arq_redis_pool = await create_pool(self.redis_settings)
            logger.info("✅ Пул подключений ARQ Redis успешно создан.")
        except Exception as e:
            logger.critical(f"❌ Ошибка при создании пула подключений ARQ Redis: {e}", exc_info=True)
            raise

    async def shutdown(self):
        """
        Корректно закрывает пул подключений ARQ Redis.
        """
        logger.info("🛑 ArqPoolManager: Запуск завершения работы пула Redis...")
        if self.arq_redis_pool:
            await self.arq_redis_pool.close()
            logger.info("✅ Пул подключений ARQ Redis закрыт.")
        else:
            logger.debug("Пул подключений ARQ Redis не был инициализирован или уже закрыт.")
        logger.info("✅ ArqPoolManager: Завершение работы выполнено.")

# Экземпляр менеджера, который будет использоваться в FastAPI
arq_pool_manager = ArqPoolManager()