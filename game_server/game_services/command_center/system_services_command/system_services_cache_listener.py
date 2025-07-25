# game_server/game_services/command_center/system_services_command/cache_request_listener.py

import json
from typing import Dict, Any
from pydantic import ValidationError
from aio_pika import IncomingMessage
import inject
import logging

from game_server.game_services.command_center.base_microservice_listener import BaseMicroserviceListener

from . import cache_request_config as config
from ....Logic.ApplicationLogic.SystemServices.cache_request_orchestrator import CacheRequestOrchestrator
from ....Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus


@inject.autoparams()
class CacheRequestCommandListener(BaseMicroserviceListener):
    """
    Слушает очередь запросов к кэшу, валидирует команды в DTO
    и передает их в CacheRequestOrchestrator для выполнения.
    """
    from ....config.settings.rabbitmq.rabbitmq_names import Queues
    SERVICE_QUEUE = Queues.SYSTEM_CACHE_REQUESTS

    MAX_CONCURRENT_TASKS = 10
    COMMAND_PROCESSING_TIMEOUT = 30

    def __init__(
        self,
        message_bus: IMessageBus,
        orchestrator: CacheRequestOrchestrator,
        logger: logging.Logger
    ):
        super().__init__(message_bus=message_bus, orchestrator=orchestrator, logger=logger)
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован для очереди: {self.SERVICE_QUEUE}")

    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Валидирует сообщение в DTO и вызывает оркестратор.
        Теперь правильно находит данные для валидации.
        """
        command_type = message_data.get("command")
        
        # ✅ ИСПРАВЛЕННАЯ ЛОГИКА (скопирована из рабочего SystemServicesListener)
        message_data_for_dto = message_data
        
        if not command_type and "payload" in message_data and isinstance(message_data["payload"], dict):
            command_type = message_data["payload"].get("command")
            if command_type:
                # Если команда нашлась внутри, то и данные для DTO тоже внутри
                message_data_for_dto = message_data["payload"]

        if not command_type:
            raise ValueError("Missing 'command' in message data or payload")
        # --- КОНЕЦ ИСПРАВЛЕННОЙ ЛОГИКИ ---

        command_info = config.CACHE_REQUEST_HANDLER_MAPPING.get(command_type)
        if not command_info:
            raise ValueError(f"No DTO mapping for command: {command_type}")
        
        dto_class = command_info["dto"]
        
        try:
            # Теперь валидируются правильные данные
            validated_dto = dto_class(**message_data_for_dto)
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}", exc_info=True)
            raise

        await self.orchestrator.process_command(validated_dto)