# game_server/Logic/InfrastructureLogic/app_mongo/app_mongo_initializer.py

import logging
from typing import Dict, Any

# Импортируем функции для работы с клиентом MongoDB
from game_server.Logic.InfrastructureLogic.app_mongo.mongo_client import get_mongo_database, init_mongo_client, close_mongo_client # 🔥 ДОБАВЛЕНО: close_mongo_client

# 🔥 УДАЛЕНО: Импорты интерфейсов и реализаций репозиториев больше не нужны здесь,
# так как они используются только в DI-модулях для связывания.
# from .repository_groups.world_state.interfaces_world_state_mongo import IWorldStateRepository, ILocationStateRepository
# from .repository_groups.world_state.world_state_repository_mongo_impl import MongoWorldStateRepositoryImpl, MongoLocationStateRepositoryImpl

from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 УДАЛЕНО: Глобальный словарь для хранения экземпляров репозиториев больше не нужен.
# _initialized_repositories: Dict[str, Any] = {}

async def initialize_mongo_repositories() -> bool:
    """
    Инициализирует клиент MongoDB.
    Вызывается один раз при старте приложения.
    """
    logger.info("🔧 Инициализация клиента MongoDB...")
    try:
        # 🔥 ИЗМЕНЕНИЕ: Вызываем инициализацию клиента MongoDB
        await init_mongo_client()
        
        # � УДАЛЕНО: Логика создания и сохранения экземпляров репозиториев перенесена в DI-контейнер.
        # db = get_mongo_database()
        # _initialized_repositories["world_state_repo"] = MongoWorldStateRepositoryImpl(db)
        # _initialized_repositories["location_state_repo"] = MongoLocationStateRepositoryImpl(db)

        logger.info("✅ Клиент MongoDB успешно инициализирован.")
        return True
    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка при инициализации клиента MongoDB: {e}", exc_info=True)
        # 🔥 ИЗМЕНЕНИЕ: Если произошла ошибка, пытаемся закрыть клиент, если он был открыт
        try:
            await close_mongo_client()
        except Exception as close_e:
            logger.error(f"Ошибка при закрытии клиента MongoDB после сбоя инициализации: {close_e}", exc_info=True)
        return False

async def shutdown_mongo_repositories() -> None:
    """
    Завершает работу клиента MongoDB.
    """
    logger.info("🛑 Завершение работы клиента MongoDB...")
    # 🔥 ИЗМЕНЕНИЕ: Вызываем функцию закрытия клиента MongoDB
    await close_mongo_client()
    logger.info("✅ Клиент MongoDB завершен.")


# 🔥 УДАЛЕНО: Все функции-геттеры для доступа к репозиториям больше не нужны.
# def get_all_mongo_repositories() -> Dict[str, Any]:
#     """Возвращает словарь со всеми инициализированными репозиториями MongoDB."""
#     if not _initialized_repositories:
#         raise RuntimeError("Репозитории MongoDB не инициализированы.")
#     return _initialized_repositories.copy()

# def get_world_state_repository() -> IWorldStateRepository:
#     """Возвращает репозиторий для статических регионов мира."""
#     try:
#         return _initialized_repositories["world_state_repo"]
#     except KeyError:
#         raise RuntimeError("Репозитории MongoDB не инициализированы или репозиторий 'world_state_repo' не найден.")

# def get_location_state_repository() -> ILocationStateRepository:
#     """Возвращает репозиторий для состояния активных локаций."""
#     try:
#         return _initialized_repositories["location_state_repo"]
#     except KeyError:
#         raise RuntimeError("Репозитории MongoDB не инициализированы.")
