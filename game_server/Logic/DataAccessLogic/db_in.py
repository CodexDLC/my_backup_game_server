
from game_server.services.logging.logging_setup import logger
import asyncpg


class AsyncDatabase:
    def __init__(self, db_url):
        """Инициализация пула соединений."""
        self.db_url = db_url
        self.pool = None  # ✅ Пул соединений
        
    async def connect(self):
        """Создаёт пул соединений к БД, с обработкой ошибок."""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(self.db_url)
                logger.info("✅ Пул соединений к БД успешно создан.")
            except Exception as e:
                logger.error(f"❌ Ошибка при создании пула соединений: {e}")
                raise RuntimeError("🔴 Невозможно установить соединение с БД")

    async def get_data(self, query: str, *params):
        """Получает данные из БД (SELECT) через пул соединений."""
        if self.pool is None:
            raise RuntimeError("🔴 Пул соединений не создан! Сначала вызови `connect()`.")

        async with self.pool.acquire() as conn:
            try:
                logger.debug(f"🔎 Выполняем SELECT: {query} | Параметры: {params}")
                rows = await conn.fetch(query, *params)
                logger.info(f"✅ Получено {len(rows)} записей.")
                return rows
            except Exception as e:
                logger.error(f"❌ Ошибка выборки данных: {e}")
                return None

    async def save_data(self, query: str, *params):
        """Сохраняет данные в БД (INSERT/UPDATE/DELETE) через пул соединений."""
        if self.pool is None:
            raise RuntimeError("🔴 Пул соединений не создан! Сначала вызови `connect()`.")

        async with self.pool.acquire() as conn:
            try:
                logger.debug(f"📤 SQL-запрос: {query} | Параметры: {params}")
                await conn.execute(query, *params)
                logger.info("✅ Данные успешно сохранены.")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения данных: {e}")

    async def disconnect(self):
        """Закрытие соединения с БД."""
        if self.pool:
            await self.pool.close()
            logger.info("🔴 Соединение с БД закрыто.")
        else:
            logger.warning("⚠ Попытка закрытия, но соединение не было установлено.")
