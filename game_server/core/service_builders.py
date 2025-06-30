# game_server/core/service_builders.py

from typing import Dict, Any
from game_server.config.logging.logging_setup import app_logger as logger

# Импортируем геттер, который дает доступ ко всем готовым зависимостям
from .dependency_aggregator import get_global_dependencies

# Импортируем специфическую логику, которую нужно будет создать
from game_server.Logic.ApplicationLogic.auth_service.AccountCreation.account_creation_logic import AccountCreator
from game_server.Logic.ApplicationLogic.auth_service.ShardManagement.shard_management_logic import ShardOrchestrator
from game_server.Logic.CoreServices.core_services_initializer import initialize_core_services, get_identifiers_service_instance

# === СБОРЩИК ДЛЯ AUTH SERVICE ===

async def build_auth_service_dependencies() -> Dict[str, Any]:
    """
    Собирает словарь зависимостей ИСКЛЮЧИТЕЛЬНО для AuthService.
    """
    logger.info("--- 🛠️ Сборка зависимостей для AuthService ---")
    
    # 1. Получаем доступ ко всем глобальным зависимостям
    global_deps = get_global_dependencies()
    
    # 2. Создаем специфические экземпляры для AuthService
    if not initialize_core_services(): # Убеждаемся, что Core-сервисы запущены
        raise RuntimeError("Ошибка инициализации Core-сервисов для AuthService.")
    
    identifiers_service = get_identifiers_service_instance()
    
    account_creator = AccountCreator(
        repository_manager=global_deps["repository_manager"],
        identifiers_service=identifiers_service,
    )
    
    shard_orchestrator = ShardOrchestrator(dependencies={
        "repository_manager": global_deps["repository_manager"],
        "shard_count_manager": global_deps["shard_count_cache_manager"],
        "message_bus": global_deps["message_bus"],
        "logger": global_deps["logger"]
    })

    # 3. Формируем финальный словарь для этого сервиса
    auth_deps = {
        # Добавляем глобальные зависимости, которые нужны напрямую
        "repository_manager": global_deps["repository_manager"],
        "message_bus": global_deps["message_bus"],
        "logger": global_deps["logger"],
        # <<< ИСПРАВЛЕНО: Добавлен недостающий session_manager
        "session_manager": global_deps["session_manager"],
        
        # Добавляем специфические зависимости
        "identifiers_service": identifiers_service,
        "account_creator": account_creator,
        "shard_manager": shard_orchestrator
    }
    logger.info("--- ✅ Зависимости для AuthService собраны ---")
    return auth_deps


# === СБОРЩИК ДЛЯ SYSTEM SERVICES ===

async def build_system_services_dependencies() -> Dict[str, Any]:
    """
    Собирает словарь зависимостей ИСКЛЮЧИТЕЛЬНО для SystemServices.
    """
    logger.info("--- 🛠️ Сборка зависимостей для SystemServices ---")
    global_deps = get_global_dependencies()
    
    # Этот сервис, судя по коду, использует только глобальные зависимости,
    # но переименовывает одну из них для своих нужд.
    system_deps = {
        "repository_manager": global_deps["repository_manager"],
        "guild_config_manager": global_deps["backend_guild_config_manager"], # Переименование
        "message_bus": global_deps["message_bus"],
        "logger": global_deps["logger"],
    }
    logger.info("--- ✅ Зависимости для SystemServices собраны ---")
    return system_deps


# === СБОРЩИК ДЛЯ GAME WORLD ORCHESTRATOR ===

async def build_game_world_dependencies() -> Dict[str, Any]:
    """
    Собирает словарь зависимостей ИСКЛЮЧИТЕЛЬНО для GameWorldOrchestrator.
    """
    logger.info("--- 🛠️ Сборка зависимостей для GameWorldOrchestrator ---")
    global_deps = get_global_dependencies()

    # Копируем ВСЕ глобальные зависимости, чтобы этот мощный сервис имел доступ ко всему.
    game_world_deps = global_deps.copy()

    logger.info("--- ✅ Зависимости для GameWorldOrchestrator собраны ---")
    return game_world_deps


# === СБОРЩИК ДЛЯ ARQ WORKER ===

async def build_arq_worker_dependencies() -> Dict[str, Any]:
    """
    Собирает словарь зависимостей для контекста ARQ воркера.
    """
    logger.info("--- 🛠️ Сборка зависимостей для ARQ Worker Context ---")
    global_deps = get_global_dependencies()
    worker_deps = global_deps.copy()
    
    # Добавляем алиас 'app_managers' для обратной совместимости с задачами ARQ.
    if "app_cache_managers" in worker_deps:
        worker_deps["app_managers"] = worker_deps["app_cache_managers"]
        
    logger.info("--- ✅ Зависимости для ARQ Worker Context собраны ---")
    return worker_deps
