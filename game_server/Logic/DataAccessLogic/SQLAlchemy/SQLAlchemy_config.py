import os

from sqlalchemy.ext.asyncio import create_async_engine
from game_server.services.logging.logging_config import loggerConfig
from game_server.settings import DATABASE_URL


# ✅ Инициализация конфигурации логирования
config = loggerConfig()
logger = config.get_logger()



# ✅ Создание движка с учетом настроек логирования из `loggerConfig`
engine = create_async_engine(
    DATABASE_URL,
    echo=config.sql_echo,  # 🔹 Управление логами SQL через конфиг
    future=True
)

# ✅ Функция проверки соединения с БД
async def test_connection():
    try:
        async with engine.connect() as conn:
            logger.info("✅ Успешное подключение к базе данных!")
    except Exception as e:
        logger.error(f"⚠ Ошибка подключения: {e}", exc_info=True)
