# game_server/game_services/command_center/auth_service_command/auth_service_rpc_handler.py

import json # Импортируем json для json.loads/dumps
import uuid # Импортируем uuid для UUID
from typing import Dict, Any, Optional
from pydantic import ValidationError

from ..base_microservice_listener import BaseMicroserviceListener

import inject
import logging

# Импорты из вашего проекта
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues
# Импорт AuthOrchestrator для типизации, если нужен
from game_server.Logic.ApplicationLogic.auth_service.auth_service import AuthOrchestrator
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus # Импорт IMessageBus для типизации

# Импортируем конфиг, где определены RPC_DTO_MAPPING
from game_server.game_services.command_center.auth_service_command import auth_service_config as config


class AuthServiceRpcHandler(BaseMicroserviceListener):
    SERVICE_QUEUE = Queues.AUTH_VALIDATE_TOKEN_RPC # Указываем конкретную очередь для валидации токенов
    MAX_CONCURRENT_TASKS = 1
    COMMAND_PROCESSING_TIMEOUT = 10.0 

    @inject.autoparams()
    def __init__(self, orchestrator: AuthOrchestrator, message_bus: IMessageBus, logger: logging.Logger):
        self.orchestrator = orchestrator
        self.message_bus = message_bus
        self.logger = logger
        
        super().__init__(message_bus=self.message_bus, orchestrator=self.orchestrator, logger=self.logger)

    async def _process_single_command(self, message_data: Dict[str, Any], original_message: Any):
        payload = message_data.get("payload", {})
        command_type = payload.get("command") # Получаем command из payload
        correlation_id = original_message.correlation_id
        reply_to = original_message.reply_to

        # Валидация наличия команды
        if not command_type:
            self.logger.error(f"RPC сообщение {original_message.delivery_tag} не содержит 'command' в payload. Payload: {payload}")
            await self._send_rpc_error_response(reply_to, correlation_id, "Missing 'command' in payload")
            raise ValueError("Missing 'command' in payload") # Это вызовет NACK сообщения

        # Поиск информации о команде в конфиге
        command_info = config.RPC_DTO_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для RPC команды не найдена конфигурация DTO: {command_type}. RPC_DTO_MAPPING keys: {list(config.RPC_DTO_MAPPING.keys())}")
            await self._send_rpc_error_response(reply_to, correlation_id, f"No DTO mapping for RPC command: {command_type}")
            raise ValueError(f"No DTO mapping for RPC command: {command_type}")
        
        request_dto_class = command_info["request_dto"]
        response_dto_class = command_info["response_dto"]

        # Валидация payload в объект DTO
        try:
            # Создаем валидированный DTO для оркестратора
            # Добавляем correlation_id, trace_id, span_id из original_message в validated_dto
            validated_dto_data = request_dto_class(**payload).model_dump()
            validated_dto_data['correlation_id'] = uuid.UUID(correlation_id) if isinstance(correlation_id, str) else correlation_id
            validated_dto_data['trace_id'] = getattr(original_message, 'trace_id', uuid.uuid4()) # Из оригинального сообщения, если есть
            validated_dto_data['span_id'] = getattr(original_message, 'span_id', None) # Из оригинального сообщения
            
            # Если RPC-запрос содержит client_id, его тоже нужно передать
            if 'client_id' in payload:
                validated_dto_data['client_id'] = payload['client_id']
                
            validated_dto = request_dto_class(**validated_dto_data)

        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для RPC команды '{command_type}': {e}. Payload: {payload}", exc_info=True)
            await self._send_rpc_error_response(reply_to, correlation_id, f"Validation error for RPC command '{command_type}': {e}")
            raise # Вызовет NACK

        # Передача валидированного DTO в оркестратор и отправка ответа
        try:
            # Orchestrator.process_rpc_command возвращает словарь с результатом (как IssueAuthTokenRpcResponseDTO)
            rpc_result_dict = await self.orchestrator.process_rpc_command(validated_dto)
            
            # Валидируем результат оркестратора в response DTO и отправляем обратно
            validated_response = response_dto_class(**rpc_result_dict)
            await self._send_rpc_response(reply_to, correlation_id, validated_response.model_dump_json())

        except Exception as e:
            self.logger.error(f"Ошибка при обработке RPC команды '{command_type}' в оркестраторе: {e}", exc_info=True)
            await self._send_rpc_error_response(reply_to, correlation_id, f"Error processing RPC command: {e}")
            raise # Вызовет NACK

    # 🔥 Методы _send_rpc_response и _send_rpc_error_response (их возвращаем)
    async def _send_rpc_response(self, reply_to: str, correlation_id: str, response_json_str: str):
        """Отправляет успешный RPC ответ."""
        # Убедитесь, что json импортирован в начале файла
        response_data_dict = json.loads(response_json_str) 
        self.logger.debug(f"DEBUG_AUTH_SERVICE_SENDING_RPC_RESPONSE: {response_data_dict}") # Лог
        await self.message_bus.publish_rpc_response(reply_to, response_data_dict, correlation_id)
        self.logger.debug(f"RPC ответ отправлен в '{reply_to}' с correlation_id: {correlation_id}")

    async def _send_rpc_error_response(self, reply_to: str, correlation_id: str, error_message: str):
        error_payload = {"error": error_message, "success": False}
        self.logger.error(f"DEBUG_AUTH_SERVICE_SENDING_RPC_ERROR_RESPONSE: {error_payload} for CorrID: {correlation_id}") # Лог
        await self.message_bus.publish_rpc_response(reply_to, error_payload, correlation_id)
        self.logger.error(f"RPC ошибка отправлена в '{reply_to}' с correlation_id: {correlation_id}: {error_message}")