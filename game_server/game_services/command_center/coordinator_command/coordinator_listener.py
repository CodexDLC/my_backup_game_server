# game_server/game_services/command_center/coordinator_command/coordinator_listener.py

import json # Добавляем импорт json для логирования и работы с данными
from typing import Dict, Any
from pydantic import ValidationError
from aio_pika import IncomingMessage # Импортируем IncomingMessage для типизации

# Импортируем базовый класс
from game_server.game_services.command_center.base_microservice_listener import BaseMicroserviceListener 

# Импортируем конфиг (для констант и маппингов)
from . import coordinator_config as config 

import inject # 🔥 НОВОЕ: Импортируем inject
import logging # 🔥 НОВОЕ: Импортируем logging для типизации

# 🔥 НОВОЕ: Предполагаем, что у вас есть CoordinatorOrchestrator
from game_server.Logic.ApplicationLogic.world_orchestrator.runtime.runtime_coordinator import RuntimeCoordinator


# 🔥 ИЗМЕНЕНИЕ: Теперь определяем константы прямо в классе (взяты из coordinator_config)
# 🔥 ИЗМЕНЕНИЕ: Добавлен декоратор @inject.autoparams()
@inject.autoparams()
class CoordinatorListener(BaseMicroserviceListener):
    """
    Слушает очередь Координатора, валидирует команды в DTO
    и передает их в CoordinatorOrchestrator для выполнения.
    """
    SERVICE_QUEUE = config.SERVICE_QUEUE # Берем из config
    MAX_CONCURRENT_TASKS = config.MAX_CONCURRENT_TASKS # Берем из config
    COMMAND_PROCESSING_TIMEOUT = config.COMMAND_PROCESSING_TIMEOUT # Берем из config

    # 🔥 ИЗМЕНЕНИЕ: Изменена сигнатура __init__ и вызов super().__init__
    def __init__(
        self, 
        message_bus: Any, # message_bus должен иметь тип IMessageBus
        orchestrator: RuntimeCoordinator, # Указываем конкретный тип оркестратора
        logger: logging.Logger # Инжектируем логгер
    ):
        # Вызов конструктора базового класса БЕЗ аргумента 'config'
        super().__init__(message_bus=message_bus, orchestrator=orchestrator, logger=logger)
        
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован для очереди: {self.SERVICE_QUEUE}")

    # 🔥 ИЗМЕНЕНИЕ: Адаптируем _process_single_command под гибкий стиль
    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Валидирует десериализованное сообщение в DTO и вызывает оркестратор.
        message_data: Десериализованные данные сообщения (dict).
        original_message: Оригинальный объект aio_pika.IncomingMessage (если нужен).
        """
        self.logger.info(f"CoordinatorListener: Получено сырое сообщение. Correlation ID: {message_data.get('correlation_id')}, "
                         f"Client ID: {message_data.get('client_id')}. Содержимое: {json.dumps(message_data)}")

        command_type = message_data.get("command")
        message_data_for_dto = message_data # По умолчанию используем весь message_data для DTO

        if not command_type:
            # Если 'command' не найден на верхнем уровне, проверяем внутри 'payload'
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

        # Используем config.COMMAND_HANDLER_MAPPING (убедитесь, что оно определено в coordinator_config.py)
        command_info = config.COMMAND_HANDLER_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для команды не найдена конфигурация DTO в COMMAND_HANDLER_MAPPING: {command_type}")
            raise ValueError(f"No DTO mapping for command: {command_type}")
        
        dto_class = command_info["dto"]

        try:
            validated_dto = dto_class(**message_data_for_dto) # Передаем подготовленные данные
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}. Данные: {json.dumps(message_data_for_dto)}", exc_info=True)
            raise

        await self.orchestrator.process_command(validated_dto)

        # 🔥 ВАЖНО: ack/nack больше НЕ НУЖНЫ здесь, они обрабатываются в base_microservice_listener.py