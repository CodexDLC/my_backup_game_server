# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/sql_config/sqlalchemy_settings.py

import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Используем ваш путь для импорта DATABASE_URL (из core_settings)
from game_server.config.settings_core import DATABASE_URL 

# 🔥 ИСПРАВЛЕНИЕ: Импортируем 'config' (экземпляр LoggerConfig) из logging_setup.py
# Файл logging_config.py больше не содержит класса loggerConfig, он был перенесен.
from game_server.config.logging.logging_setup import config as logging_config_instance 

# Используем ваш уникальный логгер


# ✅ Инициализация конфигурации логгера для получения настроек SQL_ECHO
# _logger_config_instance = loggerConfig() # ЭТА СТРОКА БОЛЬШЕ НЕ НУЖНА, МЫ ИСПОЛЬЗУЕМ ИМПОРТИРОВАННЫЙ 'config'


# ✅ Создание движка с учетом настроек логирования из `LoggerConfig`
engine = create_async_engine(
    DATABASE_URL,
    echo=logging_config_instance.sql_echo,  # 🔹 Управление логами SQL через конфиг
    poolclass=NullPool,  # <--- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: используем NullPool
    future=True
)

# engine_read (если используется) также будет здесь, используя _logger_config_instance.sql_echo
# engine_read = create_async_engine(
#     DATABASE_URL_READ,
#     echo=_logger_config_instance.sql_echo,
#     future=True
# )

# ✅ Функция test_connection перемещена в db_instance.py, т.к. это утилита проверки соединения, а не конфигурация движка.
