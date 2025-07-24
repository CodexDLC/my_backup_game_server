# game_server/Logic/ApplicationLogic/SystemServices/cache_request_orchestrator.py

import logging
from typing import Dict, Any
from pydantic import BaseModel
import inject

from game_server.game_services.command_center.system_services_command import cache_request_config

# Импортируем все необходимые DTO и конфиги
from ....contracts.shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO
from ....config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from ....Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from ....contracts.shared_models.base_responses import ErrorDetail, ResponseStatus
from ....contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload

from .handler.i_system_handler import ISystemServiceHandler


class CacheRequestOrchestrator:
    """
    Оркестратор для запросов к кэшированным данным.
    Диспетчеризует команды на соответствующие обработчики, работающие с кэшем.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        message_bus: IMessageBus,
    ):
        self.logger = logger
        self.message_bus = message_bus
        self.handlers: Dict[str, ISystemServiceHandler] = {
            command_name: inject.instance(info["handler"])
            for command_name, info in cache_request_config.CACHE_REQUEST_HANDLER_MAPPING.items()
        }
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с {len(self.handlers)} обработчиками.")

    # ✅ ИЗМЕНЕНИЕ: Сигнатура метода теперь соответствует другим оркестраторам
    async def process_command(self, validated_dto: BaseCommandDTO):
        """
        Главный метод-диспетчер. Получает DTO, находит обработчик и запускает его.
        """
        command_type = validated_dto.command
        handler = self.handlers.get(command_type)
        
        if not handler:
            self.logger.error(f"Обработчик для команды '{command_type}' не найден в {self.__class__.__name__}.")
            # ✅ ИЗМЕНЕНИЕ: Правильно формируем DTO с ошибкой
            error_result = BaseResultDTO(
                correlation_id=validated_dto.correlation_id,
                success=False,
                message=f"Обработчик для команды '{command_type}' не найден.",
                error=ErrorDetail(code="HANDLER_NOT_FOUND", message="Command handler not found."),
                client_id=validated_dto.client_id
            )
            await self._publish_response(error_result)
            return

        self.logger.info(f"Делегирование команды '{command_type}' обработчику кэша...")
        
        try:
            result_dto = await handler.process(command_dto=validated_dto)
            await self._publish_response(result_dto)
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при обработке команды '{command_type}'.")
            # ✅ ИЗМЕНЕНИЕ: Правильно формируем DTO с ошибкой
            error_result = BaseResultDTO(
                correlation_id=validated_dto.correlation_id,
                success=False,
                message=f"Ошибка сервера при обработке команды '{command_type}': {e}",
                error=ErrorDetail(code="SERVER_ERROR", message=str(e)),
                client_id=validated_dto.client_id
            )
            await self._publish_response(error_result)

    async def _publish_response(self, result_dto: BaseResultDTO):
        """
        Стандартный метод для формирования и отправки ответа через RabbitMQ.
        """
        # Этот метод полностью копируется из SystemServicesOrchestrator
        client_id_for_delivery = getattr(result_dto, 'client_id', None)
        if not client_id_for_delivery:
            self.logger.warning(f"Результат для CorrID {result_dto.correlation_id} не может быть доставлен: отсутствует client_id.")
            return
        
        response_payload = WebSocketResponsePayload(
            request_id=result_dto.correlation_id,
            status=ResponseStatus.SUCCESS if result_dto.success else ResponseStatus.FAILURE,
            message=result_dto.message,
            data=result_dto.data.model_dump() if isinstance(result_dto.data, BaseModel) else result_dto.data,
            error=result_dto.error
        )

        websocket_message = WebSocketMessage(
            type="RESPONSE",
            correlation_id=result_dto.correlation_id,
            client_id=client_id_for_delivery,
            payload=response_payload,
        )

        # Формируем ключ маршрутизации
        domain = "cache"
        action = getattr(result_dto, 'action', 'default')
        status_str = "success" if result_dto.success else "failure"
        routing_key = f"{RoutingKeys.RESPONSE_PREFIX}.{domain}.{action}.{status_str}"
        
        await self.message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=websocket_message.model_dump(mode='json')
        )
        self.logger.info(f"Ответ для CorrID {result_dto.correlation_id} опубликован в {Exchanges.EVENTS} с ключом '{routing_key}'.")