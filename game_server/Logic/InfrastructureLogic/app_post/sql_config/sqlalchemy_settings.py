# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/sql_config/sqlalchemy_settings.py

import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Используем ваш путь для импорта DATABASE_URL (из core_settings)
from game_server.config.settings_core import DATABASE_URL #

# Импортируем конфиг логгера для получения sql_echo настройки
from game_server.Logic.InfrastructureLogic.logging.logging_config import loggerConfig #

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger #

# ✅ Инициализация конфигурации логгера для получения настроек SQL_ECHO
_logger_config_instance = loggerConfig() #

# ✅ Создание движка с учетом настроек логирования из `loggerConfig`
engine = create_async_engine(
    DATABASE_URL,
    echo=_logger_config_instance.sql_echo,  # 🔹 Управление логами SQL через конфиг
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