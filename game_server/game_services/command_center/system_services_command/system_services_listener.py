# game_server/game_services/command_center/system_services_command/system_services_listener.py

from typing import Dict, Any
from pydantic import ValidationError
from aio_pika import IncomingMessage

from ..base_microservice_listener import BaseMicroserviceListener
from . import system_services_config as config

class SystemServicesCommandListener(BaseMicroserviceListener):
    # __init__ наследуется от базового класса и не требует изменений

    async def _process_single_command(self, message_data: Dict[str, Any], original_message: IncomingMessage):
        """
        Обрабатывает одну команду: находит DTO, валидирует и передает в оркестратор.
        """
        # НОВОЕ: Добавляем логирование в самом начале метода
        self.logger.info(f"Слушатель: Получено сырое сообщение. Correlation ID: {message_data.get('correlation_id')}, "
                         f"Client ID: {message_data.get('client_id')}. Содержимое: {message_data}")

        # 🔥 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Извлекаем 'command' прямо из message_data (с верхнего уровня).
        # Это соответствует тому, как команда формируется на стороне FastAPI/бота.
        command_type = message_data.get("command")

        if not command_type:
            # Если 'command' не найден на верхнем уровне, это действительно ошибка структуры сообщения.
            # Добавим дополнительную проверку на существование 'payload' и 'command' внутри него
            # для обратной совместимости, если есть старые сообщения или другие источники.
            if "payload" in message_data and isinstance(message_data["payload"], dict):
                # Если command нет на верхнем уровне, но есть payload, ищем command внутри payload
                command_type = message_data["payload"].get("command")
                if command_type:
                    # Если нашли command внутри payload, то для валидации DTO используем содержимое payload
                    # (предполагая, что payload - это и есть фактические данные DTO)
                    message_data_for_dto = message_data["payload"]
                else:
                    # Если command не найден ни на верхнем уровне, ни внутри payload
                    self.logger.error(f"Сообщение {original_message.delivery_tag} не содержит 'command' ни в корне, ни в payload.")
                    raise ValueError("Missing 'command' in message data or payload")
            else:
                # Если payload вообще нет или он не словарь
                self.logger.error(f"Сообщение {original_message.delivery_tag} не содержит 'command' в корневых данных и не имеет корректного поля 'payload'.")
                raise ValueError("Missing 'command' in message data")


        command_info = config.COMMAND_HANDLER_MAPPING.get(command_type)
        if not command_info:
            self.logger.error(f"Для команды не найдена конфигурация DTO: {command_type}")
            raise ValueError(f"No DTO mapping for command: {command_type}")
        
        dto_class = command_info["dto"]
        
        try:
            # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: Передаем message_data_for_dto (или message_data, если command на верхнем уровне) целиком в DTO.
            # Если command_type был найден на верхнем уровне, message_data_for_dto будет равен message_data.
            # Если command_type был найден внутри payload, message_data_for_dto будет равен message_data["payload"].
            validated_dto = dto_class(**(message_data_for_dto if 'message_data_for_dto' in locals() else message_data))
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO для команды '{command_type}': {e}")
            raise

        await self.orchestrator.process_command(validated_dto)

