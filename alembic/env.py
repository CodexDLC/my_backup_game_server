
from sqlalchemy import create_engine, pool
from alembic import context
from logging.config import fileConfig
from datetime import datetime
from game_server.database.models.models import Base
from game_server.services.logging.logging_setup import logger
from game_server.settings import DATABASE_URL_SYNC




# Конфигурация Alembic
config = context.config
fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", DATABASE_URL_SYNC)

# Импорт моделей

target_metadata = Base.metadata

def log_step(message: str, level: str = "info"):
    """Логирование с временными метками"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    getattr(logger, level)(log_message)

def run_migrations_online():
    """Запуск миграций без обработки `seeds`"""
    log_step("🚀 Начало онлайн-миграций")

    try:
        log_step(f"Попытка подключения к БД: {DATABASE_URL_SYNC}")
        engine = create_engine(DATABASE_URL_SYNC, poolclass=pool.NullPool, echo=True)

        with engine.connect() as connection:
            log_step("🔌 Подключение успешно")

            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                include_schemas=True
            )

            log_step("🔍 Запуск транзакции миграций")
            with context.begin_transaction():
                context.run_migrations()
                log_step("✅ Миграции успешно выполнены")

            log_step("🏁 Все операции завершены")

    except Exception as e:
        log_step(f"🔥 Ошибка миграции: {str(e)}", "critical")
        raise

if context.is_offline_mode():
    log_step("⚡ OFFLINE-режим: генерация SQL")
    try:
        context.configure(
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        context.run_migrations()
        log_step("✅ OFFLINE-миграции сгенерированы")
    except Exception as e:
        log_step(f"❌ Ошибка OFFLINE-миграции: {str(e)}", "critical")
        raise
else:
    run_migrations_online()
