# game_server/game_services/command_center/coordinator_command/coordinator_listener.py

from typing import Dict, Any
from pydantic import ValidationError
from aio_pika import IncomingMessage # 🔥 НОВЫЙ ИМПОРТ: IncomingMessage для типизации

# Импортируем базовый класс
from game_server.game_services.command_center.base_microservice_listener import BaseMicroserviceListener 

# Импортируем конфиг
from . import coordinator_config as config 


class CoordinatorListener(BaseMicroserviceListener):
    """
    Слушает очередь Координатора, валидирует команды в DTO
    и передает их в CoordinatorOrchestrator для выполнения.
    """
    def __init__(self, message_bus, config, orchestrator: Any): # orchestrator: CoordinatorOrchestrator (можно добавить для типизации)
        super().__init__(message_bus=message_bus, config=config, orchestrator=orchestrator)
        
        self.orchestrator = orchestrator 
        self.logger.info("✅ CoordinatorListener инициализирован с CoordinatorOrchestrator.")

    # 🔥 ИСПРАВЛЕНИЕ: Изменена сигнатура метода _process_single_command
    # Теперь принимает message_data (словарь) и original_message (IncomingMessage)
    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Валидирует десериализованное сообщение в DTO и вызывает оркестратор.
        message_data: Десериализованные данные сообщения (dict).
        original_message: Оригинальный объект aio_pika.IncomingMessage (если нужен).
        """
        # Теперь payload берется напрямую из message_data (который уже словарь)
        payload = message_data.get("payload", {})
        command_type = payload.get("command") # Предполагается, что 'command' находится в 'payload'

        # Ищем DTO-класс в конфиге
        command_info = config.COMMAND_HANDLER_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для команды не найдена конфигурация DTO: {command_type}")
            raise ValueError(f"Для команды не найдена конфигурация DTO: {command_type}")
        
        dto_class = command_info["dto"]

        # Валидируем
        try:
            # Pydantic-валидация и создание DTO
            validated_dto = dto_class(**payload)
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}", exc_info=True)
            raise

        # Передаем готовый DTO в оркестратор
        await self.orchestrator.process_command(validated_dto)

        # 🔥 ВАЖНО: ack/nack больше НЕ НУЖНЫ здесь, они обрабатываются в base_microservice_listener.py