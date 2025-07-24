# game_server/core/di_modules/system_service_bindings.py
# Version: 0.004 (Добавлены все связывания для обработчиков SystemServices)

import inject
import logging
from typing import Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession # Добавлен для фабрик репозиториев

# Импорты System Services Orchestrator
from game_server.Logic.ApplicationLogic.SystemServices.cache_request_orchestrator import CacheRequestOrchestrator
from game_server.Logic.ApplicationLogic.SystemServices.handler_cache_requests.get_location_summary_handler import GetLocationSummaryCommandHandler
from game_server.Logic.ApplicationLogic.SystemServices.system_services_orchestrator import SystemServicesOrchestrator


# 🔥 ИМПОРТЫ ВСЕХ ОБРАБОТЧИКОВ ИЗ СТРУКТУРЫ handler
# Обработчики для домена "account"
from game_server.Logic.ApplicationLogic.SystemServices.handler.account.create_new_character_handler import CreateNewCharacterHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.account.get_character_list_for_account_handler import GetCharacterListForAccountHandler

# Обработчики для домена "admin"
from game_server.Logic.ApplicationLogic.SystemServices.handler.admin.reload_cache_handler import AdminReloadCacheHandler

# Обработчики для домена "discord"
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.create_single_entity_handler import CreateSingleEntityHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.delete_config_from_bot_handler import DeleteConfigFromBotHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.delete_entities_handler import DeleteDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.get_entities_handler import GetDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.sync_config_from_bot_handler import SyncConfigFromBotHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.sync_entities_handler import SyncDiscordEntitiesHandler

# Обработчики для домена "shard"
from game_server.Logic.ApplicationLogic.SystemServices.handler.shard.admin_save_shard_handler import AdminSaveShardHandler

# Обработчики для домена "state_entity"
from game_server.Logic.ApplicationLogic.SystemServices.handler.state_entity.get_all_state_entities_handler import GetAllStateEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.state_entity.get_state_entity_by_key_handler import GetStateEntityByKeyHandler

# Обработчики для домена "world_map"
from game_server.Logic.ApplicationLogic.SystemServices.handler.world_map.get_world_data_handler import GetWorldDataHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.add_player_to_state_handler import AddPlayerToStateHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.get_location_summary_handler import GetLocationSummaryHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.remove_player_from_state_handler import RemovePlayerFromStateHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.location_state_orchestrator import LocationStateOrchestrator


def configure_system_services(binder):
    """
    Конфигурирует связывания для системных сервисов.
    Все обработчики SystemServices явно привязываются к DI-контейнеру.
    """
    # SystemServicesOrchestrator (не работает с БД, делегирует)
    binder.bind_to_constructor(SystemServicesOrchestrator, SystemServicesOrchestrator)

    # 🔥 СВЯЗЫВАНИЕ ВСЕХ ОБРАБОТЧИКОВ SystemServices
    # Эти обработчики используют @inject.autoparams() в своих конструкторах
    # и управляют своими транзакциями через @transactional на методе process.

    # Account Handlers
    binder.bind_to_constructor(CreateNewCharacterHandler, CreateNewCharacterHandler)
    binder.bind_to_constructor(GetCharacterListForAccountHandler, GetCharacterListForAccountHandler)

    # Admin Handlers
    binder.bind_to_constructor(AdminReloadCacheHandler, AdminReloadCacheHandler)

    # Discord Handlers
    binder.bind_to_constructor(CreateSingleEntityHandler, CreateSingleEntityHandler)
    binder.bind_to_constructor(DeleteConfigFromBotHandler, DeleteConfigFromBotHandler)
    binder.bind_to_constructor(DeleteDiscordEntitiesHandler, DeleteDiscordEntitiesHandler)
    binder.bind_to_constructor(GetDiscordEntitiesHandler, GetDiscordEntitiesHandler)
    binder.bind_to_constructor(SyncConfigFromBotHandler, SyncConfigFromBotHandler)
    binder.bind_to_constructor(SyncDiscordEntitiesHandler, SyncDiscordEntitiesHandler)

    # Shard Handlers
    binder.bind_to_constructor(AdminSaveShardHandler, AdminSaveShardHandler)

    # State Entity Handlers
    binder.bind_to_constructor(GetAllStateEntitiesHandler, GetAllStateEntitiesHandler)
    binder.bind_to_constructor(GetStateEntityByKeyHandler, GetStateEntityByKeyHandler)

        # 🔥 НОВОЕ: Связывание для LocationStateOrchestrator
    binder.bind_to_constructor(LocationStateOrchestrator, LocationStateOrchestrator)

    # 🔥 НОВОЕ: Связывание обработчиков LocationStateManagement
    binder.bind_to_constructor(AddPlayerToStateHandler, AddPlayerToStateHandler)
    binder.bind_to_constructor(RemovePlayerFromStateHandler, RemovePlayerFromStateHandler)
    binder.bind_to_constructor(GetLocationSummaryHandler, GetLocationSummaryHandler)
        # ✅ НОВАЯ ПРИВЯЗКА: Регистрируем новый оркестратор
    binder.bind_to_constructor(CacheRequestOrchestrator, CacheRequestOrchestrator)

    # ✅ НОВАЯ ПРИВЯЗКА: Регистрируем новый обработчик для кэша
    binder.bind_to_constructor(GetLocationSummaryCommandHandler, GetLocationSummaryCommandHandler)

    # World Map Handlers
    binder.bind_to_constructor(GetWorldDataHandler, GetWorldDataHandler)
    
    