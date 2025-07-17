# --- Файл: game_server/game_services/command_center/auth_service_command/auth_service_config.py ---

# Импортируем DTO, которые использует этот сервис

from game_server.Logic.ApplicationLogic.auth_service.Handlers.login_character_by_id_handler import LoginCharacterByIdHandler

# Импортируем имя очереди из центральной топологии
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues

# Импортируем обработчики
from game_server.Logic.ApplicationLogic.auth_service.Handlers.discord_hub_handler import DiscordHubHandler
from game_server.contracts.dtos.auth.commands import HubRoutingCommandDTO, IssueAuthTokenRpcCommandDTO, LoginCharacterByIdCommandDTO, ValidateTokenRpcCommandDTO
from game_server.contracts.dtos.auth.results import IssueAuthTokenRpcResponseDTO, ValidateTokenRpcResponseDTO






# --- Обязательные параметры для BaseMicroserviceListener ---
SERVICE_QUEUE = Queues.AUTH_COMMANDS
MAX_CONCURRENT_TASKS = 100
COMMAND_PROCESSING_TIMEOUT = 10.0

# НОВЫЕ КОНСТАНТЫ для RPC команд
RPC_COMMAND_ISSUE_AUTH_TOKEN = "issue_auth_token"
RPC_COMMAND_VALIDATE_TOKEN = "validate_token_rpc"

# --- Константы для команд ---
COMMAND_DISCORD_HUB_REGISTERED = "discord_hub_registered"
COMMAND_LOGIN_CHARACTER_BY_ID = "character_login_by_id"


# --- Карта для команд ---
COMMAND_DTO_MAPPING = {
    COMMAND_DISCORD_HUB_REGISTERED: {"handler": DiscordHubHandler, "dto": HubRoutingCommandDTO},
    # ▼▼▼ ПЕРЕМЕЩЕНО СЮДА ИЗ RPC_DTO_MAPPING ▼▼▼
    COMMAND_LOGIN_CHARACTER_BY_ID: {"handler": LoginCharacterByIdHandler, "dto": LoginCharacterByIdCommandDTO},
}

# ДОБАВЛЕНО: Карта для RPC-команд
RPC_DTO_MAPPING = {
    RPC_COMMAND_ISSUE_AUTH_TOKEN: {
        "request_dto": IssueAuthTokenRpcCommandDTO,
        "response_dto": IssueAuthTokenRpcResponseDTO
    },
    RPC_COMMAND_VALIDATE_TOKEN: {
        "request_dto": ValidateTokenRpcCommandDTO,
        "response_dto": ValidateTokenRpcResponseDTO
    },
}