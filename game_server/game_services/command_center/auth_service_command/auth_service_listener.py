# game_server/game_services/command_center/auth_service_command/auth_service_listener.py

import asyncio
import json
import logging
from typing import Dict, Any
import inject
from aio_pika import IncomingMessage
from pydantic import ValidationError # Добавляем импорт ValidationError

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO
from game_server.game_services.command_center.auth_service_command.auth_service_config import COMMAND_DTO_MAPPING
from game_server.game_services.command_center.base_microservice_listener import BaseMicroserviceListener
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues


# Используем COMMAND_DTO_MAPPING из auth_service_config

from game_server.Logic.ApplicationLogic.auth_service.command_orchestrator import AuthCommandOrchestrator

class AuthServiceCommandListener(BaseMicroserviceListener):
    # Константы конфигурации для базового класса
    SERVICE_QUEUE = Queues.AUTH_COMMANDS # Используем константу очереди
    MAX_CONCURRENT_TASKS = 100 # Примерное значение, можно взять из auth_service_config, если там есть
    COMMAND_PROCESSING_TIMEOUT = 10.0 # Примерное значение, можно взять из auth_service_config, если там есть

    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        message_bus: IMessageBus,
        orchestrator: AuthCommandOrchestrator,
    ):
        super().__init__(message_bus=message_bus, orchestrator=orchestrator, logger=logger)
        self.logger.info(f"AuthServiceCommandListener инициализирован для очереди: {self.SERVICE_QUEUE}")

    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Обрабатывает одну команду, поддерживая два формата сообщений:
        1. Новый (вложенный payload).
        2. Старый (плоский, для обратной совместимости).
        """
        self.logger.info(f"AuthListener: Получено сырое сообщение. Correlation ID: {message_data.get('correlation_id')}, "
                         f"Client ID: {message_data.get('client_id')}.")
        self.logger.debug(f"Полное содержимое: {json.dumps(message_data)}")

        command_type = None
        message_data_for_dto = None

        # Сначала проверяем новый, предпочтительный формат (вложенный)
        if "payload" in message_data and isinstance(message_data["payload"], dict) and "command" in message_data["payload"]:
            self.logger.debug("Обнаружена новая (вложенная) структура сообщения.")
            message_data_for_dto = message_data["payload"]
            command_type = message_data_for_dto.get("command")
        
        # Если не нашли, проверяем старый, плоский формат
        elif "command" in message_data:
            self.logger.debug("Обнаружена старая (плоская) структура сообщения для обратной совместимости.")
            message_data_for_dto = message_data
            command_type = message_data.get("command")

        # Если после всех проверок команда не найдена, это ошибка
        if not command_type:
            self.logger.error(f"Сообщение {original_message.delivery_tag} не содержит поле 'command' в известном формате.")
            raise ValueError("Missing 'command' in a recognizable message structure")

        # Используем COMMAND_DTO_MAPPING для получения класса DTO
        command_info = COMMAND_DTO_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для команды не найдена конфигурация DTO в COMMAND_DTO_MAPPING: {command_type}")
            raise ValueError(f"No DTO mapping for command: {command_type}")

        dto_class = command_info["dto"]

        # Валидация и передача в оркестратор
        try:
            validated_dto: BaseCommandDTO = dto_class(**message_data_for_dto)
            self.logger.debug(f"Сообщение команды '{command_type}' успешно валидировано в DTO.")
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}. Данные: {json.dumps(message_data_for_dto)}", exc_info=True)
            raise

        await self.orchestrator.process_command(validated_dto)
        self.logger.info(f"Команда '{command_type}' с correlation_id: {validated_dto.correlation_id} успешно обработана оркестратором.")
