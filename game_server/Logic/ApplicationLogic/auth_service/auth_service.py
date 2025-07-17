# game_server/Logic/ApplicationLogic/auth_service/auth_service.py

import logging
import uuid
from typing import Dict, Any
import inject


from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload
from .Handlers.auth_issue_token_rpc_handler import AuthIssueTokenRpcHandler
from .Handlers.auth_validate_token_rpc_handler import AuthValidateTokenRpcHandler

class AuthOrchestrator:
    """
    Упрощенный оркестратор для обработки RPC-команд аутентификации.
    Делегирует всю работу специализированным обработчикам.
    """
    @inject.autoparams() # <-- ВОТ ТАК ПРАВИЛЬНО: БЕЗ СПИСКА АРГУМЕНТОВ
    def __init__(
        self,
        # logger: logging.Logger, # <--- УБИРАЕМ логгер из параметров конструктора
        message_bus: IMessageBus,
        issue_token_handler: AuthIssueTokenRpcHandler,
        validate_token_handler: AuthValidateTokenRpcHandler
    ):
        self.logger = inject.instance(logging.Logger) # <-- ЯВНО получаем логгер через inject.instance()
        self.message_bus = message_bus
        self.rpc_handlers = {
            "issue_auth_token": issue_token_handler,
            "validate_token_rpc": validate_token_handler,
        }
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с {len(self.rpc_handlers)} RPC-обработчиками.")

    async def process_rpc_command(self, validated_rpc_dto: BaseCommandDTO) -> Dict[str, Any]:
        command_type = validated_rpc_dto.command
        self.logger.info(f"Обработка RPC команды: '{command_type}'.")

        handler = self.rpc_handlers.get(command_type)
        if not handler:
            error_payload = {"success": False, "error": "Handler not found", "error_code": "HANDLER_NOT_FOUND"}
            await self._publish_rpc_response(error_payload, validated_rpc_dto)
            return error_payload

        try:
            result_dict = await handler.process(validated_rpc_dto)
            await self._publish_rpc_response(result_dict, validated_rpc_dto)
            return result_dict
        except Exception as e:
            self.logger.exception(f"Критическая ошибка в RPC-оркестраторе при команде '{command_type}': {e}")
            error_payload = {"success": False, "error": str(e), "error_code": "INTERNAL_ORCHESTRATOR_ERROR"}
            await self._publish_rpc_response(error_payload, validated_rpc_dto)
            return error_payload

    async def _publish_rpc_response(self, result_data: Dict[str, Any], request_dto: BaseCommandDTO):
        is_success = result_data.get("success", False) or result_data.get("is_valid", False)
        message = result_data.get("message") or ("Success" if is_success else result_data.get("error", "Error"))
        
        response_payload = WebSocketResponsePayload(
            request_id=request_dto.correlation_id,
            status=ResponseStatus.SUCCESS if is_success else ResponseStatus.FAILURE,
            message=message,
            data=result_data
        )
        websocket_message = WebSocketMessage(
            type="RESPONSE",
            correlation_id=request_dto.correlation_id,
            trace_id=request_dto.trace_id,
            span_id=request_dto.span_id,
            client_id=getattr(request_dto, 'client_id', None),
            payload=response_payload
        )
        await self.message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=f"rpc.response.{request_dto.command}",
            message=websocket_message.model_dump(mode='json')
        )
        self.logger.info(f"Ответ на RPC команду '{request_dto.command}' отправлен.")