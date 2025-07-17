# game_server/Logic/ApplicationLogic/auth_service/command_orchestrator.py

import logging
import os
from typing import Dict, Any, Callable # Добавлено Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession # Добавлено AsyncSession

# Импорты специфичные для CommandOrchestrator

from game_server.Logic.ApplicationLogic.auth_service.Handlers.login_character_by_id_handler import LoginCharacterByIdHandler
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.shard_management_logic import ShardOrchestrator
from game_server.Logic.CoreServices.services.identifiers_servise import IdentifiersServise
from game_server.Logic.DomainLogic.auth_service_logic.AccountCreation.account_creation_logic import AccountCreator
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count.shard_count_cache_manager import ShardCountCacheManager


from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail, ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload

# Импорты хендлеров
from .Handlers.i_auth_handler import IAuthHandler
from .Handlers.discord_hub_handler import DiscordHubHandler



class AuthCommandOrchestrator:
    """
    Оркестратор для сервиса аутентификации, обрабатывающий обычные команды (не RPC),
    такие как логин и регистрация.
    """
    @inject.autoparams() # <-- ВОТ ТАК ПРАВИЛЬНО: БЕЗ СПИСКА АРГУМЕНТОВ
    def __init__(
        self,
        # logger: logging.Logger, # <--- УБИРАЕМ логгер из параметров конструктора
        message_bus: IMessageBus,
        session_manager: ISessionManager,
        shard_count_cache_manager: ShardCountCacheManager,
        identifiers_service: IdentifiersServise,
        account_creator: AccountCreator,
        shard_orchestrator: ShardOrchestrator,
        discord_hub_handler: DiscordHubHandler,
        login_character_by_id_handler: LoginCharacterByIdHandler
    ):
        self.logger = inject.instance(logging.Logger) # <-- ЯВНО получаем логгер через inject.instance()
        self.message_bus = message_bus
        self.session_manager = session_manager
        self.shard_count_cache_manager = shard_count_cache_manager
        self.identifiers_service = identifiers_service
        self.account_creator = account_creator
        self.shard_orchestrator = shard_orchestrator

        self.handlers: Dict[str, IAuthHandler] = {
            "discord_hub_registered": discord_hub_handler,          
            "character_login_by_id": login_character_by_id_handler,
        }
        
        self.logger.info(f"✅ AuthCommandOrchestrator инициализирован с {len(self.handlers)} обработчиками.")
        self.logger.debug("DEBUG: AuthCommandOrchestrator завершил инициализацию.")

    async def process_command(self, validated_command_dto: BaseCommandDTO) -> None:
        """
        Диспетчеризует обычные команды на соответствующие обработчики (Handlers).
        Формирует и публикует WebSocket-ответ для Gateway.
        """
        command_type = validated_command_dto.command
        self.logger.info(f"INFO: Обработка обычной команды: '{command_type}'.")
        self.logger.debug(f"DEBUG: Полный DTO для команды '{command_type}': {validated_command_dto.model_dump_json()}")

        handler = self.handlers.get(command_type)
        if handler:
            try:
                result_dto: BaseResultDTO = await handler.process(validated_command_dto)
                self.logger.info(f"INFO: Команда '{command_type}' обработана. Результат: {result_dto.success}, {result_dto.message}")

                websocket_response_payload = WebSocketResponsePayload(
                    request_id=validated_command_dto.correlation_id,
                    status=ResponseStatus.SUCCESS if result_dto.success else ResponseStatus.FAILURE,
                    message=result_dto.message,
                    data=result_dto.data.model_dump() if result_dto.data else {},
                    error=result_dto.error if result_dto.error else None
                )
                
                websocket_message = WebSocketMessage(
                    type="RESPONSE",
                    correlation_id=validated_command_dto.correlation_id,
                    trace_id=validated_command_dto.trace_id,
                    span_id=validated_command_dto.span_id,
                    client_id=getattr(validated_command_dto, 'client_id', None),
                    payload=websocket_response_payload,
                    target_audience="DISCORD_BOT"
                )
                
                status_key = "success" if result_dto.success else "failure"
                standardized_routing_key = f"response.auth.{command_type}.{status_key}"

                await self.message_bus.publish(
                    exchange_name=Exchanges.EVENTS,
                    routing_key=standardized_routing_key,
                    message=websocket_message.model_dump(mode='json')
                )
                self.logger.info(f"INFO: WebSocket-ответ для команды '{command_type}' опубликован в RabbitMQ с ключом '{standardized_routing_key}'.")

            except Exception as e:
                self.logger.error(f"ERROR: Ошибка при выполнении обработчика для команды '{command_type}': {e}", exc_info=True)
                error_response_payload = WebSocketResponsePayload(
                    request_id=validated_command_dto.correlation_id,
                    status=ResponseStatus.FAILURE,
                    message=f"Ошибка обработки команды '{command_type}': {str(e)}",
                    error=ErrorDetail(code="HANDLER_EXCEPTION", message=str(e))
                )
                error_websocket_message = WebSocketMessage(
                    type="RESPONSE",
                    correlation_id=validated_command_dto.correlation_id,
                    payload=error_response_payload,
                    client_id=getattr(validated_command_dto, 'client_id', None)
                )
                
                error_routing_key = f"response.auth.{command_type}.error"
                await self.message_bus.publish(
                    exchange_name=Exchanges.EVENTS,
                    routing_key=error_routing_key,
                    message=error_websocket_message.model_dump(mode='json')
                )
                raise
        else:
            self.logger.warning(f"WARNING: Неизвестная команда: '{command_type}'. DTO: {validated_command_dto.model_dump_json()}")
            unknown_command_response = WebSocketResponsePayload(
                request_id=validated_command_dto.correlation_id,
                status=ResponseStatus.FAILURE,
                message=f"Неизвестная команда: {command_type}",
                error=ErrorDetail(code="UNKNOWN_COMMAND", message=f"Обработчик для команды '{command_type}' не найден.")
            )
            unknown_command_ws_message = WebSocketMessage(
                type="RESPONSE",
                correlation_id=validated_command_dto.correlation_id,
                payload=unknown_command_response,
                client_id=getattr(validated_command_dto, 'client_id', None)
            )
            
            unknown_command_routing_key = f"response.auth.{command_type}.unknown"
            await self.message_bus.publish(
                exchange_name=Exchanges.EVENTS,
                routing_key=unknown_command_routing_key,
                message=unknown_command_ws_message.model_dump(mode='json')
            )
            raise ValueError(f"Unknown command: {command_type}")