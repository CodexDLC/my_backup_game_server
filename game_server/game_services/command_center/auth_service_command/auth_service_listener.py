# game_server/game_services/command_center/auth_service_command/auth_service_listener.py

from typing import Dict, Any
from pydantic import ValidationError
from aio_pika import IncomingMessage

# Импортируем наш новый, надежный базовый класс
from ..base_microservice_listener import BaseMicroserviceListener
# Импортируем конфиг, чтобы знать, какие команды мы обрабатываем
from . import auth_service_config as config

class AuthServiceCommandListener(BaseMicroserviceListener):
    """
    Стандартизированный слушатель команд для AuthService.
    Реализует _process_single_command для валидации и передачи команд в оркестратор.
    """
    # __init__ наследуется от базового класса и не требует изменений

    # СТАНДАРТ: Реализуем ТОЛЬКО этот метод. Вся остальная логика (ack/nack, таймауты)
    # находится в базовом классе.
    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Обрабатывает одну команду: находит DTO, валидирует и передает в оркестратор.
        """
        # 1. Извлекаем payload и определяем тип команды
        # Мы доверяем, что message_data уже является словарем после msgpack.unpackb
        payload = message_data.get("payload", {})
        command_type = payload.get("command") # Используем универсальное поле 'command'

        if not command_type:
            self.logger.error(f"Сообщение {original_message.delivery_tag} не содержит 'command' в payload.")
            raise ValueError("Missing 'command' in payload")

        # 2. Находим соответствующий DTO в нашем конфиге
        command_info = config.COMMAND_DTO_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для команды не найдена конфигурация DTO: {command_type}")
            raise ValueError(f"No DTO mapping for command: {command_type}")
        
        dto_class = command_info["dto"]

        # 3. Валидируем payload в объект DTO
        try:
            validated_dto = dto_class(**payload)
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}")
            # Выбрасываем исключение, чтобы базовый класс сделал nack()
            raise

        # 4. Передаем готовый, валидированный DTO в оркестратор
        # self.orchestrator был передан в конструкторе при создании слушателя
        await self.orchestrator.process_command(validated_dto)
