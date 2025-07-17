# game_server/game_services/command_center/system_services_command/system_services_config.py
# Version: 0.002 (Обновлена для новых обработчиков и команд)

# --- 1. Импорты DTO из "common_contracts" ---

# DTO для команд управления шардами
# DTO для команд интеграции с Discord
# DTO для команд State Entity

# 🔥 ИЗМЕНЕНО: Импорты новых DTO команд
from game_server.Logic.ApplicationLogic.SystemServices.handler.account.logout_character_handler import LogoutCharacterHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.game_command.move_character_to_location_handler import MoveCharacterToLocationHandler
from game_server.contracts.dtos.game_commands.navigation_commands import MoveToLocationCommandDTO
from game_server.contracts.dtos.system.commands import GetCharacterListForAccountCommandDTO, LogoutCharacterCommandDTO
from game_server.contracts.dtos.character.commands import CreateNewCharacterCommandDTO


# --- 2. Импорты Обработчиков (Handlers) из папки "handler" ---
from game_server.Logic.ApplicationLogic.SystemServices.handler.shard.admin_save_shard_handler import AdminSaveShardHandler

# Обработчики для домена "discord"
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.sync_entities_handler import SyncDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.delete_entities_handler import DeleteDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.create_single_entity_handler import CreateSingleEntityHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.get_entities_handler import GetDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.sync_config_from_bot_handler import SyncConfigFromBotHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.delete_config_from_bot_handler import DeleteConfigFromBotHandler

# Обработчики для домена "state_entity"
from game_server.Logic.ApplicationLogic.SystemServices.handler.state_entity.get_all_state_entities_handler import GetAllStateEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.state_entity.get_state_entity_by_key_handler import GetStateEntityByKeyHandler

# Обработчики для домена "admin"
from game_server.Logic.ApplicationLogic.SystemServices.handler.admin.reload_cache_handler import AdminReloadCacheHandler

# Обработчики для домена "world_map"
from game_server.Logic.ApplicationLogic.SystemServices.handler.world_map.get_world_data_handler import GetWorldDataHandler

# 🔥 ИЗМЕНЕНО: Импорты новых/переименованных обработчиков для аккаунтов/персонажей
from game_server.Logic.ApplicationLogic.SystemServices.handler.account.get_character_list_for_account_handler import GetCharacterListForAccountHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.account.create_new_character_handler import CreateNewCharacterHandler


# --- 3. Импорты для RabbitMQ ---
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues
from game_server.contracts.api_models.discord.config_management_requests import GuildConfigDeleteRequest, GuildConfigSyncRequest
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntityBatchDeleteRequest
from game_server.contracts.dtos.admin.commands import ReloadCacheCommandDTO
from game_server.contracts.dtos.discord.commands import DiscordEntitiesSyncCommand, DiscordEntityCreateCommand, GetDiscordEntitiesCommandDTO
from game_server.contracts.dtos.game_world.commands import GetWorldDataCommandDTO
from game_server.contracts.dtos.shard.commands import SaveShardCommandDTO
from game_server.contracts.dtos.state_entity.commands import GetAllStateEntitiesCommand, GetStateEntityByKeyCommand


# --- 4. Конфигурация Слушателя (без изменений) ---
SERVICE_QUEUE = Queues.SYSTEM_COMMANDS
MAX_CONCURRENT_TASKS = 50
COMMAND_PROCESSING_TIMEOUT = 10.0

# Константы команд
# Команды для Shard
COMMAND_SAVE_SHARD = "system:save_shard"

# Команды для Discord
COMMAND_DISCORD_SYNC_ENTITIES = "system:sync_discord_entities"
COMMAND_STATE_ENTITY_GET_ALL = "system:get_all_state_entities"
COMMAND_STATE_ENTITY_GET_BY_KEY = "state_entity:get_by_key"
COMMAND_DISCORD_DELETE_ENTITIES = "discord:batch_delete_entities"
COMMAND_DISCORD_CREATE_SINGLE_ENTITY = "discord:create_single_entity"
COMMAND_DISCORD_GET_ENTITIES = "discord:get_entities"
COMMAND_DISCORD_SYNC_CONFIG = "discord:sync_config_from_bot"
COMMAND_DISCORD_DELETE_CONFIG = "discord:delete_config_from_bot"

# НОВАЯ КОНСТАНТА КОМАНДЫ: Для получения статических данных мира
COMMAND_GET_WORLD_DATA = "get_world_data"
COMMAND_ADMIN_RELOAD_CACHE = "admin:reload_cache"

# 🔥 ИЗМЕНЕНО: Новые константы команд для аккаунтов/персонажей
COMMAND_GET_CHARACTER_LIST_FOR_ACCOUNT = "get_character_list_for_account"
COMMAND_CREATE_NEW_CHARACTER = "create_new_character"
COMMAND_LOGOUT_CHARACTER = "logout_character"

# гейм команд 
COMMAND_MOVE_CHARACTER_TO_LOCATION = "move_character_to_location"


# Главный словарь
COMMAND_HANDLER_MAPPING = {
    # Команды для Shard
    COMMAND_SAVE_SHARD: {"handler": AdminSaveShardHandler, "dto": SaveShardCommandDTO},

    # Команды для Discord
    COMMAND_DISCORD_SYNC_ENTITIES: {"handler": SyncDiscordEntitiesHandler, "dto": DiscordEntitiesSyncCommand},
    COMMAND_DISCORD_DELETE_ENTITIES: {"handler": DeleteDiscordEntitiesHandler, "dto": UnifiedEntityBatchDeleteRequest},
    COMMAND_DISCORD_CREATE_SINGLE_ENTITY: {"handler": CreateSingleEntityHandler, "dto": DiscordEntityCreateCommand},
    COMMAND_DISCORD_GET_ENTITIES: {"handler": GetDiscordEntitiesHandler, "dto": GetDiscordEntitiesCommandDTO},
    COMMAND_DISCORD_SYNC_CONFIG: {"handler": SyncConfigFromBotHandler, "dto": GuildConfigSyncRequest},
    COMMAND_DISCORD_DELETE_CONFIG: {"handler": DeleteConfigFromBotHandler, "dto": GuildConfigDeleteRequest},
    
    # Команды для State Entity
    COMMAND_STATE_ENTITY_GET_ALL: {"handler": GetAllStateEntitiesHandler, "dto": GetAllStateEntitiesCommand},
    COMMAND_STATE_ENTITY_GET_BY_KEY: {"handler": GetStateEntityByKeyHandler, "dto": GetStateEntityByKeyCommand},

    # Команды для Admin
    COMMAND_ADMIN_RELOAD_CACHE: {"handler": AdminReloadCacheHandler, "dto": ReloadCacheCommandDTO},

    # Команды для World Data
    COMMAND_GET_WORLD_DATA: {"handler": GetWorldDataHandler, "dto": GetWorldDataCommandDTO},

    # 🔥 ИЗМЕНЕНО: Добавлены новые/переименованные команды и их обработчики/DTO
    COMMAND_GET_CHARACTER_LIST_FOR_ACCOUNT: {"handler": GetCharacterListForAccountHandler, "dto": GetCharacterListForAccountCommandDTO},
    COMMAND_CREATE_NEW_CHARACTER: {"handler": CreateNewCharacterHandler, "dto": CreateNewCharacterCommandDTO},
    COMMAND_LOGOUT_CHARACTER: {"handler": LogoutCharacterHandler, "dto": LogoutCharacterCommandDTO},
    COMMAND_MOVE_CHARACTER_TO_LOCATION: {"handler": MoveCharacterToLocationHandler, "dto": MoveToLocationCommandDTO},
    
}