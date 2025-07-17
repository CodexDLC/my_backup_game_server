# game_server/core/di_modules/mongo_bindings.py

import inject
from typing import Any
from pymongo.mongo_client import MongoClient # ДОБАВЛЕНО: Импорт MongoClient

# Импорты интерфейсов и реализаций MongoDB репозиториев
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.character_cache.interfaces_character_cache_mongo import IMongoCharacterCacheRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.character_cache.mongo_character_cache_repository_impl import MongoCharacterCacheRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository, IWorldStateRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.world_state_repository_mongo_impl import MongoLocationStateRepositoryImpl, MongoWorldStateRepositoryImpl


def configure_mongo_repositories(binder):
    """
    Конфигурирует связывания для всех репозиториев MongoDB.
    Они биндятся как прямые экземпляры, получающие MongoClient через inject.autoparams.
    """
    # Регистрация репозиториев MongoDB (интерфейс к реализации)
    # Теперь они используют bind_to_constructor, что позволяет inject автоматически внедрять MongoClient
    binder.bind_to_constructor(IWorldStateRepository, MongoWorldStateRepositoryImpl)
    binder.bind_to_constructor(ILocationStateRepository, MongoLocationStateRepositoryImpl)
    binder.bind_to_constructor(IMongoCharacterCacheRepository, MongoCharacterCacheRepositoryImpl)
    # ... другие Mongo репозитории, если есть
