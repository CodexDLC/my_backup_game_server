import glob
import os
import sys
from sqlalchemy import create_engine, pool, text
from alembic import context
from logging.config import fileConfig


# Импорт глобального логгера
from game_server.services.logging.logging_setup import logger
from game_server.settings import DATABASE_URL_SYNC

# Пути
here = os.path.dirname(__file__)
project_root = os.path.dirname(here)
sys.path.insert(0, project_root)
SEEDS_DIR = os.path.join(project_root, "game_server", "database", "schemas", "seeds")

# Конфигурация Alembic
config = context.config
fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", DATABASE_URL_SYNC)

# Импорт моделей
from game_server.database.models.models import Base
target_metadata = Base.metadata


def run_migrations_online():
    """Запускает онлайн-миграции Alembic, используя синхронный движок."""
    logger.info("🚀 [Alembic] Запуск онлайн-миграций...")
    try:
        engine = create_engine(DATABASE_URL_SYNC, poolclass=pool.NullPool)
        with engine.connect() as connection:
            logger.info("🔌 Подключение к БД успешно установлено.")
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()
                logger.info("✅ Миграции успешно выполнены!")

            for path in sorted(glob.glob(os.path.join(SEEDS_DIR, "*.sql"))):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        sql = f.read()
                    connection.execute(text(sql))
                    logger.info(f"🌱 Сид успешно загружен: {os.path.basename(path)}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при выполнении сида {os.path.basename(path)}: {e}")
    except Exception as e:
        logger.critical(f"🔥 Ошибка в процессе миграции: {e}")


if context.is_offline_mode():
    logger.info("⚡ [Alembic] OFFLINE-режим: генерация SQL без подключения к БД.")
    try:
        context.run_migrations()
        logger.info("✅ Миграции OFFLINE завершены.")
    except Exception as e:
        logger.critical(f"❌ Ошибка при OFFLINE-миграции: {e}")
else:
    run_migrations_online()
