from sqlalchemy import create_engine, pool
from alembic import context
from logging.config import fileConfig
from datetime import datetime

from game_server.config.settings_core import DATABASE_URL_SYNC, SQL_ECHO
from game_server.database.models.models import Base
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# 👇 ИЗМЕНЕНИЕ: Импортируем URL для БД и настройку echo из главного файла настроек



# Конфигурация Alembic
config = context.config

# Эта строка уже не нужна, если fileConfig ниже используется
# fileConfig(config.config_file_name) 

# Устанавливаем URL для подключения к БД
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
        # 👇 ИЗМЕНЕНИЕ: Используем настройку SQL_ECHO
        engine = create_engine(DATABASE_URL_SYNC, poolclass=pool.NullPool, echo=SQL_ECHO)

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
            url=DATABASE_URL_SYNC, # Добавляем URL и для оффлайн режима
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
        log_step("✅ OFFLINE-миграции сгенерированы")
    except Exception as e:
        log_step(f"❌ Ошибка OFFLINE-миграции: {str(e)}", "critical")
        raise
else:
    run_migrations_online()