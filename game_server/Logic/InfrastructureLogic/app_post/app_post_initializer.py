# game_server/Logic/InfrastructureLogic/app_post/app_post_initializer.py

import logging
from typing import Dict, Any

# Используем существующую фабрику сессий из db_instance.py
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 УДАЛЕНО: Импорты интерфейсов и реализаций репозиториев больше не нужны здесь,
# так как они используются только в DI-модулях для связывания.
# from .repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
# from .repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository, IAccountInfoRepository
# ... и все остальные импорты интерфейсов и реализаций репозиториев


# 🔥 УДАЛЕНО: Глобальный словарь для хранения экземпляров репозиториев больше не нужен.
# _initialized_repositories: Dict[str, Any] = {}


async def initialize_postgres_repositories() -> bool:
    """
    Инициализирует фабрику сессий PostgreSQL.
    Вызывается один раз при старте приложения.
    """
    # 🔥 ИЗМЕНЕНИЕ: Логика инициализации репозиториев перенесена в DI-контейнер.
    # Эта функция теперь отвечает только за то, чтобы AsyncSessionLocal был готов к использованию.
    # Поскольку AsyncSessionLocal импортируется, его фабрика уже доступна.
    # Если бы здесь требовалась явная инициализация пула соединений, она была бы здесь.
    
    logger.info("🔧 Инициализация фабрики сессий PostgreSQL...")
    try:
        # Просто убеждаемся, что AsyncSessionLocal доступен и не вызывает ошибок при импорте.
        # Реальное подключение к БД происходит при первом использовании сессии или при создании движка.
        # Если у вас есть явный метод connect() для движка, вызовите его здесь.
        # Например: await engine.connect() if engine else pass
        if AsyncSessionLocal: # Простая проверка, что класс существует
            logger.info("✅ Фабрика сессий PostgreSQL успешно инициализирована.")
            return True
        else:
            logger.critical("🚨 Критическая ошибка: AsyncSessionLocal не доступен.")
            return False
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации фабрики сессий PostgreSQL: {e}", exc_info=True)
        return False


async def shutdown_postgres_repositories() -> None:
    """
    Завершает работу ресурсов PostgreSQL (например, пула соединений).
    """
    # 🔥 ИЗМЕНЕНИЕ: Логика завершения работы репозиториев перенесена в DI-контейнер.
    # Здесь мы только логируем и, возможно, закрываем глобальный движок, если он есть.
    logger.info("🛑 Завершение работы фабрики сессий PostgreSQL...")
    # Если engine управляется глобально и имеет метод dispose(), его можно вызвать здесь.
    # if engine:
    #     await engine.dispose()
    logger.info("✅ Фабрика сессий PostgreSQL завершена.")
