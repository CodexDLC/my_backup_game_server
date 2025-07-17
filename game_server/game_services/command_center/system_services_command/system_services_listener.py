# game_server/game_services/command_center/system_services_command/system_services_listener.py

import json
from typing import Dict, Any
from pydantic import ValidationError
from aio_pika import IncomingMessage

from game_server.game_services.command_center.base_microservice_listener import BaseMicroserviceListener
from . import system_services_config as config 

import inject
import logging

# Импорт конкретных классов для DI
from game_server.Logic.ApplicationLogic.SystemServices.system_services_orchestrator import SystemServicesOrchestrator
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus # <-- ДОБАВЛЕН ИМПОРТ


@inject.autoparams()
class SystemServicesCommandListener(BaseMicroserviceListener):
    """
    Слушает очередь Системных Сервисов, валидирует команды в DTO
    и передает их в SystemServicesOrchestrator для выполнения.
    """
    SERVICE_QUEUE = config.SERVICE_QUEUE
    MAX_CONCURRENT_TASKS = config.MAX_CONCURRENT_TASKS
    COMMAND_PROCESSING_TIMEOUT = config.COMMAND_PROCESSING_TIMEOUT

    def __init__(
        self, 
        message_bus: IMessageBus, # <-- ИСПРАВЛЕНО: Any заменен на IMessageBus
        orchestrator: SystemServicesOrchestrator,
        logger: logging.Logger
    ):
        super().__init__(message_bus=message_bus, orchestrator=orchestrator, logger=logger)
        
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован для очереди: {self.SERVICE_QUEUE}")

    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Валидирует десериализованное сообщение в DTO и вызывает оркестратор.
        """
        self.logger.info(f"SystemListener: Получено сырое сообщение. Correlation ID: {message_data.get('correlation_id')}, "
                         f"Client ID: {message_data.get('client_id')}. Содержимое: {json.dumps(message_data)}")

        command_type = message_data.get("command")
        message_data_for_dto = message_data

        if not command_type:
            if "payload" in message_data and isinstance(message_data["payload"], dict):
                command_type = message_data["payload"].get("command")
                if command_type:
                    message_data_for_dto = message_data["payload"]
                else:
                    self.logger.error(f"Сообщение {original_message.delivery_tag} не содержит 'command' ни в корне, ни в payload.")
                    raise ValueError("Missing 'command' in message data or payload")
            else:
                self.logger.error(f"Сообщение {original_message.delivery_tag} не содержит 'command' в корневых данных и не имеет корректного поля 'payload'.")
                raise ValueError("Missing 'command' in message data")

        command_info = config.COMMAND_HANDLER_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для команды не найдена конфигурация DTO в COMMAND_HANDLER_MAPPING: {command_type}")
            raise ValueError(f"No DTO mapping for command: {command_type}")
        
        dto_class = command_info["dto"]
        
        try:
            validated_dto = dto_class(**message_data_for_dto)
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}. Данные: {json.dumps(message_data_for_dto)}", exc_info=True)
            raise

        await self.orchestrator.process_command(validated_dto)
