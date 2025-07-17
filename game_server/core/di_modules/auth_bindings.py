# game_server/core/di_modules/auth_bindings.py

import inject

# Импортируем все классы, которые нужно будет создавать
# 🔥 Оставляем AuthIssueTokenRpcHandler, AuthValidateTokenRpcHandler, DiscordHubHandler, LoginCharacterByIdHandler
#    как обработчики бизнес-логики, если они используются Orchestrator'ами
from game_server.Logic.ApplicationLogic.auth_service.Handlers.auth_issue_token_rpc_handler import AuthIssueTokenRpcHandler
from game_server.Logic.ApplicationLogic.auth_service.Handlers.auth_validate_token_rpc_handler import AuthValidateTokenRpcHandler
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator
from game_server.Logic.ApplicationLogic.auth_service.command_orchestrator import AuthCommandOrchestrator

# Импорты обычных обработчиков (бизнес-логики)
from game_server.Logic.ApplicationLogic.auth_service.Handlers.discord_hub_handler import DiscordHubHandler
from game_server.Logic.ApplicationLogic.auth_service.Handlers.login_character_by_id_handler import LoginCharacterByIdHandler


# Импорты логики, которая используется в обработчиках
from game_server.Logic.DomainLogic.auth_service_logic.AccountCreation.account_creation_logic import AccountCreator
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.shard_management_logic import ShardOrchestrator

# 🔥 НОВЫЕ ИМПОРТЫ: Слушатели RabbitMQ
from game_server.game_services.command_center.auth_service_command.auth_issue_token_rpc import AuthIssueTokenRpc
from game_server.game_services.command_center.auth_service_command.auth_service_listener import AuthServiceCommandListener
from game_server.game_services.command_center.auth_service_command.auth_service_rpc_handler import AuthServiceRpcHandler



def configure_auth_services(binder):
    """
    Конфигурирует все зависимости для auth_service.
    """
    # --- Оркестраторы (они инжектируют обработчики бизнес-логики) ---
    binder.bind_to_constructor(AuthOrchestrator, AuthOrchestrator)
    binder.bind_to_constructor(AuthCommandOrchestrator, AuthCommandOrchestrator)

    # --- Обработчики RPC (бизнес-логики, используемые AuthOrchestrator) ---
    # Эти классы, которые находятся в Logic/ApplicationLogic/auth_service/Handlers
    binder.bind_to_constructor(AuthIssueTokenRpcHandler, AuthIssueTokenRpcHandler)
    binder.bind_to_constructor(AuthValidateTokenRpcHandler, AuthValidateTokenRpcHandler)

    # --- Обработчики обычных команд (бизнес-логики, используемые AuthCommandOrchestrator) ---
    binder.bind_to_constructor(DiscordHubHandler, DiscordHubHandler)
    binder.bind_to_constructor(LoginCharacterByIdHandler, LoginCharacterByIdHandler)


    # --- Вспомогательные классы/логика ---
    binder.bind_to_constructor(AccountCreator, AccountCreator)
    binder.bind_to_constructor(ShardOrchestrator, ShardOrchestrator)

    # 🔥 НОВЫЕ ПРИВЯЗКИ: Слушатели RabbitMQ (используемые в auth_service_main.py)
    # Они получают оркестраторы, message_bus и logger через inject.autoparams
    binder.bind_to_constructor(AuthServiceCommandListener, AuthServiceCommandListener)
    binder.bind_to_constructor(AuthServiceRpcHandler, AuthServiceRpcHandler)
    binder.bind_to_constructor(AuthIssueTokenRpc, AuthIssueTokenRpc) # Привязка для переименованного класса