




from game_server.Logic.DomainLogic.CharacterLogic.character_creation import finalize_character_creation
from game_server.services.logging.logging_setup import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.app_cache.redis_client import RedisClient




class Character:
    def __init__(self):
        """Инициализация подключений"""

        try:
            self.db_session = None  # Сессию получим в процессе работы
            self.redis = RedisClient()  # ✅ Инкапсулированный клиент Redis
            logger.info("Инициализация Character завершена.")
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {e}")

    async def init_redis(self):
        """Инициализация и проверка подключения к Redis"""
        if not await self.redis.ping():
            logger.error("Ошибка подключения к Redis: сервер не отвечает")
            raise ConnectionError("Redis connection failed")
        logger.info("Redis успешно подключен.")

    async def run(self):
        """Запуск основной логики персонажа"""
        logger.info("Запуск логики персонажа...")

        await self.init_redis()  # Убедимся, что Redis подключен

        async for session in get_db_session():
            self.db_session = session

            # Здесь будет основной процесс работы персонажа
            # Например, вызовы генерации параметров, навыков, статов

            # Завершаем создание персонажа
            await finalize_character_creation(self.character_id, self.db_session, self.redis)

    

    async def close_connections(self):
        """Закрытие подключений"""
        if self.db_session:
            await self.db_session.close()
            logger.info("Сессия базы данных закрыта.")

async def main():
    """Функция запуска"""
    character = Character()
    await character.run()
    await character.close_connections()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
