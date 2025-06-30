# game_server/game_services/command_center/system_services_command/system_services_config.py

# --- 1. Импорты DTO из "common_contracts" ---

# DTO для команд управления шардами
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.sync_config_from_bot_handler import SyncConfigFromBotHandler
# Добавлен импорт GuildConfigDeleteRequest для DTO
from game_server.common_contracts.api_models.discord_api import GuildConfigSyncRequest, UnifiedEntityBatchDeleteRequest, GuildConfigDeleteRequest
from game_server.common_contracts.dtos.shard_dtos import SaveShardCommandDTO, ShardOperationResultDTO, NotifyAdminsCommandDTO

# DTO для команд интеграции с Discord
from game_server.common_contracts.dtos.discord_dtos import DiscordEntitiesDeleteCommand, DiscordEntitiesSyncCommand, DiscordEntityCreateCommand, GetDiscordEntitiesCommandDTO

# DTO для команд State Entity
from game_server.common_contracts.dtos.state_entity_dtos import GetAllStateEntitiesCommand, GetStateEntityByKeyCommand


# --- 2. Импорты Обработчиков (Handlers) из папки "handler" ---
from game_server.Logic.ApplicationLogic.SystemServices.handler.shard.admin_save_shard_handler import AdminSaveShardHandler

# Обработчики для домена "discord"
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.sync_entities_handler import SyncDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.delete_entities_handler import DeleteDiscordEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.create_single_entity_handler import CreateSingleEntityHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.get_entities_handler import GetDiscordEntitiesHandler
# НОВЫЙ ИМПОРТ: Обработчик для удаления конфигурации гильдии
from game_server.Logic.ApplicationLogic.SystemServices.handler.discord.delete_config_from_bot_handler import DeleteConfigFromBotHandler


# Обработчики для домена "state_entity"
from game_server.Logic.ApplicationLogic.SystemServices.handler.state_entity.get_all_state_entities_handler import GetAllStateEntitiesHandler
from game_server.Logic.ApplicationLogic.SystemServices.handler.state_entity.get_state_entity_by_key_handler import GetStateEntityByKeyHandler


# --- 3. Импорты для RabbitMQ ---
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues


# --- 4. Конфигурация Слушателя (без изменений) ---
SERVICE_QUEUE = Queues.SYSTEM_COMMANDS
MAX_CONCURRENT_TASKS = 50
COMMAND_PROCESSING_TIMEOUT = 10.0

# --- 5. Константы и Карта Команд ---

COMMAND_SAVE_SHARD = "system:save_shard"
COMMAND_DISCORD_SYNC_ENTITIES = "system:sync_discord_entities"
COMMAND_STATE_ENTITY_GET_ALL = "system:get_all_state_entities"
COMMAND_STATE_ENTITY_GET_BY_KEY = "state_entity:get_by_key"
COMMAND_DISCORD_DELETE_ENTITIES = "discord:batch_delete_entities"
COMMAND_DISCORD_CREATE_SINGLE_ENTITY = "discord:create_single_entity"
COMMAND_DISCORD_GET_ENTITIES = "discord:get_entities"
COMMAND_DISCORD_SYNC_CONFIG = "discord:sync_config_from_bot"
# НОВАЯ КОНСТАНТА КОМАНДЫ: Для удаления конфигурации гильдии
COMMAND_DISCORD_DELETE_CONFIG = "discord:delete_config_from_bot"


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
    # НОВЫЙ МАППИНГ: Для команды удаления конфигурации гильдии
    COMMAND_DISCORD_DELETE_CONFIG: {"handler": DeleteConfigFromBotHandler, "dto": GuildConfigDeleteRequest},
    
    # Команды для State Entity
    COMMAND_STATE_ENTITY_GET_ALL: {"handler": GetAllStateEntitiesHandler, "dto": GetAllStateEntitiesCommand},
    COMMAND_STATE_ENTITY_GET_BY_KEY: {"handler": GetStateEntityByKeyHandler, "dto": GetStateEntityByKeyCommand},
}
