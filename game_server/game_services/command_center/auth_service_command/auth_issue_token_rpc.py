# game_server/game_services/command_center/auth_service_command/auth_issue_token_rpc.py

import json
from typing import Dict, Any, Optional
from pydantic import ValidationError

from ..base_microservice_listener import BaseMicroserviceListener

import inject
import logging

# Импорты из вашего проекта
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues
from game_server.game_services.command_center.auth_service_command import auth_service_config as config
# 🔥 ВАЖНО: Импортируем конкретный тип для оркестратора
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator 
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus


# 🔥 ИЗМЕНЕНО: Класс переименован на AuthIssueTokenRpc
class AuthIssueTokenRpc(BaseMicroserviceListener): 
    SERVICE_QUEUE = Queues.AUTH_ISSUE_BOT_TOKEN_RPC
    MAX_CONCURRENT_TASKS = 1
    COMMAND_PROCESSING_TIMEOUT = 10.0 

    @inject.autoparams()
    # 🔥 ИЗМЕНЕНИЕ: Указываем КОНКРЕТНЫЙ ТИП для orchestrator (AuthOrchestrator вместо Any)
    def __init__(self, orchestrator: AuthOrchestrator, message_bus: IMessageBus, logger: logging.Logger):
        self.orchestrator = orchestrator
        self.message_bus = message_bus
        self.logger = logger
        
        # Передаем конкретные экземпляры в super().__init__
        super().__init__(message_bus=self.message_bus, orchestrator=self.orchestrator, logger=self.logger)
        self.logger.info(f"AuthIssueTokenRpc инициализирован для очереди: {self.SERVICE_QUEUE}")
        self.logger.debug(f"DEBUG: AuthIssueTokenRpc инициализирован с оркестратором: {type(orchestrator).__name__}")


    async def _process_single_command(self, message_data: Dict[str, Any], original_message: Any):
        self.logger.debug(f"DEBUG: Получено сырое сообщение RPC для обработки. Delivery Tag: {original_message.delivery_tag}")
        
        payload = message_data.get("payload", {})
        command_type = payload.get("command")
        correlation_id = original_message.correlation_id
        reply_to = original_message.reply_to

        self.logger.info(f"INFO: Начинается обработка RPC команды: '{command_type}'. Correlation ID: {correlation_id}.")
        self.logger.debug(f"DEBUG: Полный payload RPC сообщения: {payload}")

        if not command_type:
            self.logger.error(f"ERROR: RPC сообщение {original_message.delivery_tag} не содержит 'command' в payload. Payload: {payload}")
            await self._send_rpc_error_response(reply_to, correlation_id, "Missing 'command' in payload", "MISSING_COMMAND")
            raise ValueError("Missing 'command' in payload")

        command_info = config.RPC_DTO_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"ERROR: Для RPC команды не найдена конфигурация DTO: {command_type}. Доступные ключи: {list(config.RPC_DTO_MAPPING.keys())}")
            await self._send_rpc_error_response(reply_to, correlation_id, f"No DTO mapping for RPC command: {command_type}", "NO_DTO_MAPPING")
            raise ValueError(f"No DTO mapping for RPC command: {command_type}")
        
        request_dto_class = command_info["request_dto"]
        response_dto_class = command_info["response_dto"]
        self.logger.debug(f"DEBUG: Найдены DTO для команды '{command_type}': Request={request_dto_class.__name__}, Response={response_dto_class.__name__}")

        try:
            validated_dto = request_dto_class(**payload) 
            self.logger.debug(f"DEBUG: Payload успешно валидирован в DTO: {validated_dto.__class__.__name__}")

        except ValidationError as e:
            self.logger.error(f"ERROR: Ошибка валидации DTO для RPC команды '{command_type}': {e}. Payload: {payload}", exc_info=True)
            await self._send_rpc_error_response(reply_to, correlation_id, f"Validation error for RPC command '{command_type}': {e}", "DTO_VALIDATION_ERROR")
            raise

        try:
            rpc_result = await self.orchestrator.process_rpc_command(validated_dto)
            self.logger.debug(f"DEBUG: Оркестратор успешно обработал команду '{command_type}'. Результат: {rpc_result}")
            
            if not isinstance(rpc_result, dict):
                self.logger.error(f"ERROR: Оркестратор вернул не словарь для команды '{command_type}'. Тип: {type(rpc_result).__name__}. Результат: {rpc_result}")
                await self._send_rpc_error_response(reply_to, correlation_id, "Orchestrator returned invalid response type", "ORCHESTRATOR_BAD_RESPONSE")
                raise ValueError("Orchestrator returned invalid response type")

            validated_response = response_dto_class(**rpc_result)
            self.logger.debug(f"DEBUG: Результат оркестратора успешно валидирован в DTO: {validated_response.__class__.__name__}")
            await self._send_rpc_response(reply_to, correlation_id, validated_response.model_dump_json())
            self.logger.info(f"INFO: RPC ответ для команды '{command_type}' успешно отправлен.")

        except Exception as e:
            self.logger.critical(f"CRITICAL: Критическая ошибка при обработке RPC команды '{command_type}' в оркестраторе: {e}", exc_info=True)
            error_code = getattr(e, 'code', 'UNEXPECTED_ERROR')
            error_message_for_client = getattr(e, 'message', str(e))
            await self._send_rpc_error_response(reply_to, correlation_id, f"Error processing RPC command: {error_message_for_client}", error_code)
            raise

    async def _send_rpc_response(self, reply_to: str, correlation_id: str, response_json_str: str):
        """Отправляет успешный RPC ответ."""
        response_data_dict = json.loads(response_json_str) 
        self.logger.debug(f"DEBUG_AUTH_SERVICE_SENDING_RPC_RESPONSE: {response_data_dict}") 
        
        try:
            await self.message_bus.publish_rpc_response(reply_to, response_data_dict, correlation_id)
            self.logger.debug(f"DEBUG: RPC ответ отправлен в '{reply_to}' с correlation_id: {correlation_id}")
        except Exception as e:
            self.logger.critical(f"CRITICAL: Ошибка при публикации RPC ответа в '{reply_to}' для correlation_id: {correlation_id}: {e}", exc_info=True)

    async def _send_rpc_error_response(self, reply_to: str, correlation_id: str, error_message: str, error_code: str = "GENERIC_ERROR"):
        """Отправляет RPC ответ с ошибкой."""
        error_payload = {"error": error_message, "success": False, "error_code": error_code}
        self.logger.error(f"ERROR: RPC ошибка отправлена в '{reply_to}' с correlation_id: {correlation_id}: {error_message} (Code: {error_code})")
        try:
            await self.message_bus.publish_rpc_response(reply_to, error_payload, correlation_id)
        except Exception as e:
            self.logger.critical(f"CRITICAL: Ошибка при публикации RPC ответа об ошибке в '{reply_to}' для correlation_id: {correlation_id}: {e}", exc_info=True)
