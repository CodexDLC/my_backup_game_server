# game_server/api_fast/dependencies.py

from fastapi import Depends, HTTPException, WebSocket, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict # Добавлена Dict

# ===================================================================
# 1. ИМПОРТЫ
# ===================================================================

# --- Импорты для InfrastructureLogic (DB и Cache) ---
from game_server.Logic.InfrastructureLogic.db_instance import get_db_session # Оставляем для других сервисов, которым нужна прямая сессия
from game_server.Logic.InfrastructureLogic.app_post.app_post_initializer import get_repository_manager_instance # Предполагаем, что эта функция существует
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # Добавлен

from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import get_initialized_app_cache_managers, central_redis_client_instance
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient

# --- Импорты интерфейсов для Кэша (теперь из папки interfaces) ---
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_character_cache import ICharacterCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_item_cache import IItemCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_redis_batch_store import IRedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_cache import IReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_task_queue_cache import ITaskQueueCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_tick_cache import ITickCacheManager


# --- Импорты для Сервисов Бизнес-Логики (из ApplicationLogic) ---
from game_server.Logic.ApplicationLogic.api_reg.auth_service import AuthService
from game_server.Logic.ApplicationLogic.DiscordIntegration.discord_binding_logic import DiscordBindingLogic # Обновлен путь
from game_server.Logic.ApplicationLogic.DiscordIntegration.Discord_State_Entities_logic import StateEntitiesDiscordLogic # Обновлен путь
from game_server.Logic.ApplicationLogic.DiscordIntegration.state_entities_logic import StateEntitiesLogic # Обновлен путь
# from game_server.Logic.PresentationLayer.system_route_logic.system_gameworld_logic import SystemGameWorldLogic # УДАЛЕНО

from game_server.Logic.DomainLogic.utils.export_service import ExportService # Если ExportService не использует repo/cache, его можно оставить так

# --- Импорты для Шлюза ---
from game_server.api_fast.gateway.connection_manager import ConnectionManager


# ===================================================================
# 2. ЗАВИСИМОСТИ ДЛЯ INFRASTRUCTURE (DB и Cache)
# ===================================================================

def get_repository_manager() -> RepositoryManager:
    """Зависимость FastAPI для получения инициализированного RepositoryManager."""
    return get_repository_manager_instance() # Функция из app_post_initializer

def get_cache_managers() -> Dict[str, Any]:
    """Зависимость FastAPI для получения словаря инициализированных менеджеров кэша."""
    return get_initialized_app_cache_managers()

def get_redis_client() -> CentralRedisClient:
    """Зависимость FastAPI для получения инициализированного CentralRedisClient."""
    if central_redis_client_instance is None:
        raise RuntimeError("CentralRedisClient не был инициализирован. Убедитесь, что lifespan startup event запущен.")
    return central_redis_client_instance

# --- Провайдеры для конкретных менеджеров кэша, использующие их интерфейсы ---
def get_redis_batch_store_dep() -> IRedisBatchStore:
    """Зависимость FastAPI для получения инициализированного RedisBatchStore."""
    return get_cache_managers()['redis_batch_store']

def get_task_queue_cache_manager_dep() -> ITaskQueueCacheManager:
    """Зависимость FastAPI для получения инициализированного TaskQueueCacheManager."""
    return get_cache_managers()['task_queue_cache_manager']

def get_character_cache_manager_dep() -> ICharacterCacheManager:
    """Зависимость FastAPI для получения инициализированного CharacterCacheManager."""
    return get_cache_managers()['character_cache_manager']

def get_item_cache_manager_dep() -> IItemCacheManager:
    """Зависимость FastAPI для получения инициализированного ItemCacheManager."""
    return get_cache_managers()['item_cache_manager']

def get_reference_data_cache_manager_dep() -> IReferenceDataCacheManager:
    """Зависимость FastAPI для получения инициализированного ReferenceDataCacheManager."""
    return get_cache_managers()['reference_data_cache_manager']

def get_reference_data_reader_dep() -> IReferenceDataReader:
    """Зависимость FastAPI для получения инициализированного ReferenceDataReader."""
    return get_cache_managers()['reference_data_reader']

def get_tick_cache_manager_dep() -> ITickCacheManager:
    """Зависимость FastAPI для получения инициализированного TickCacheManager."""
    return get_cache_managers()['tick_cache_manager']



# ===================================================================
# 3. ЗАВИСИМОСТИ ДЛЯ СЕРВИСОВ БИЗНЕС-ЛОГИКИ
# ===================================================================

def get_auth_service(
    repo_manager: RepositoryManager = Depends(get_repository_manager),
    cache_managers: Dict[str, Any] = Depends(get_cache_managers)
) -> AuthService:
    """Провайдер для сервиса аутентификации."""
    # Предполагаем, что AuthService теперь принимает RepositoryManager и cache_managers
    return AuthService(repo_manager, cache_managers)

# УДАЛЕНО: def get_gameworld_service(...), так как SystemGameWorldLogic удален

def get_discord_binding_logic(
    repo_manager: RepositoryManager = Depends(get_repository_manager),
    cache_managers: Dict[str, Any] = Depends(get_cache_managers)
) -> DiscordBindingLogic:
    """Провайдер для логики привязок Discord."""
    # DiscordBindingLogic теперь принимает RepositoryManager и cache_managers
    return DiscordBindingLogic(repo_manager, cache_managers)

def get_state_entities_discord_logic(
    repo_manager: RepositoryManager = Depends(get_repository_manager),
    cache_managers: Dict[str, Any] = Depends(get_cache_managers)
) -> StateEntitiesDiscordLogic:
    """Провайдер для логики сущностей состояний Discord."""
    # StateEntitiesDiscordLogic теперь принимает RepositoryManager и cache_managers
    return StateEntitiesDiscordLogic(repo_manager, cache_managers)

def get_state_entities_logic(
    repo_manager: RepositoryManager = Depends(get_repository_manager),
    cache_managers: Dict[str, Any] = Depends(get_cache_managers)
) -> StateEntitiesLogic:
    """Провайдер для общей логики сущностей состояний."""
    # StateEntitiesLogic теперь принимает RepositoryManager и cache_managers
    return StateEntitiesLogic(repo_manager, cache_managers)

def get_export_service(
    # Если ExportService использует Repo/Cache, добавьте зависимости
    # repo_manager: RepositoryManager = Depends(get_repository_manager),
    # cache_managers: Dict[str, Any] = Depends(get_cache_managers)
) -> ExportService:
    """Провайдер для сервиса экспорта."""
    # Если ExportService не использует Repo/Cache, его конструктор не меняется
    return ExportService()


# ===================================================================
# 4. ПРОЧИЕ ЗАВИСИМОСТИ (например, для заголовков)
# ===================================================================

async def get_auth_token(request: Request) -> str:
    """Извлекает Bearer токен из заголовка Authorization."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не предоставлен Bearer токен аутентификации."
        )
    return auth_header.split(" ")[1]


# ===================================================================
# 5. ЗАВИСИМОСТИ ДЛЯ СЕРВИСОВ ШЛЮЗА
# ===================================================================

def get_connection_manager(request: Request) -> ConnectionManager: # ИЗМЕНЕНО: принимает Request
    """
    Возвращает синглтон-экземпляр ConnectionManager из состояния приложения.
    (Экземпляр будет создан и помещен в app.state при старте).
    """
    if not hasattr(request.app.state, 'connection_manager'): # ИЗМЕНЕНО: используем request.app.state
        raise RuntimeError("ConnectionManager не был инициализирован в lifespan.")
    return request.app.state.connection_manager # ИЗМЕНЕНО: используем request.app.state