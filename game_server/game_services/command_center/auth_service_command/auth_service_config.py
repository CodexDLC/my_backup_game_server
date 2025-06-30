# game_server/game_services/command_center/auth_service_command/auth_service_config.py

# Импортируем DTO, которые использует этот сервис
# 🔥 ИЗМЕНЕНИЕ: Импортируем стандартизированные DTO с их новыми названиями
from game_server.common_contracts.dtos.auth_dtos import (
    HubRoutingCommandDTO,
    DiscordShardLoginCommandDTO
)

# Импортируем имя очереди из центральной топологии
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues

# 🔥 ИЗМЕНЕНИЕ: Импортируем обработчики
from game_server.Logic.ApplicationLogic.auth_service.Handlers.discord_hub_handler import DiscordHubHandler
from game_server.Logic.ApplicationLogic.auth_service.Handlers.discord_shard_login_handler import DiscordShardLoginHandler

# --- Обязательные параметры для BaseMicroserviceListener ---
SERVICE_QUEUE = Queues.AUTH_COMMANDS  # Указываем, какую очередь слушать
MAX_CONCURRENT_TASKS = 100
COMMAND_PROCESSING_TIMEOUT = 10.0 # Это уже было


# 🔥 НОВЫЕ/ОБНОВЛЕННЫЕ КОНСТАНТЫ КОМАНД (должны совпадать с полем 'command' в DTO)
COMMAND_DISCORD_HUB_LOGIN = "discord_hub_login"
COMMAND_DISCORD_SHARD_LOGIN = "discord_shard_login"


# --- Специфичные параметры для логики AuthServiceListener ---
# Карта, которая связывает 'command' из сообщения с DTO-классом и классом обработчика
COMMAND_DTO_MAPPING = {
    # 🔥 ИСПРАВЛЕНИЕ: Правильное сопоставление команд с обработчиками и DTO
    COMMAND_DISCORD_HUB_LOGIN: {"handler": DiscordHubHandler, "dto": HubRoutingCommandDTO},
    COMMAND_DISCORD_SHARD_LOGIN: {"handler": DiscordShardLoginHandler, "dto": DiscordShardLoginCommandDTO},
}