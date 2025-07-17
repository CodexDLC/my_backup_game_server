# game_server/core/di_modules/core_service_bindings.py

import inject
import logging
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты Core Services
from game_server.Logic.CoreServices.services.identifiers_servise import IdentifiersServise
from game_server.Logic.CoreServices.services.random_service import RandomService
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager # 🔥 ДОБАВЛЕНО: Импорт DataVersionManager

# Импорты зависимостей, которые нужны Core Services (теперь это фабрики репозиториев)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
# 🔥 ДОБАВЛЕНО: Импорт для фабрики репозитория версий данных
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository


def configure_core_services(binder):
    """
    Конфигурирует связывания для Core-сервисов.
    Сервисы, зависящие от PostgreSQL репозиториев, инжектируют их фабрики.
    Теперь все привязки используют bind_to_constructor.
    """
    # Core Services (синглтоны)
    # IdentifiersServise (является транзакционной границей через декоратор)
    # 🔥 ИЗМЕНЕНО: Используем bind_to_constructor
    binder.bind_to_constructor(IdentifiersServise, IdentifiersServise)
    
    # RandomService (не работает с БД)
    # 🔥 ИЗМЕНЕНО: Используем bind_to_constructor
    binder.bind_to_constructor(RandomService, RandomService)

    # 🔥 ДОБАВЛЕНО: DataVersionManager теперь привязывается как обычный сервис
    binder.bind_to_constructor(DataVersionManager, DataVersionManager)
