# game_server/Logic/ApplicationLogic/SystemServices/system_services_orchestrator.py

import logging
from typing import Dict, Any, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO
from game_server.common_contracts.shared_models.api_contracts import WebSocketMessage, WebSocketResponsePayload, ResponseStatus, ErrorDetail
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus

from game_server.game_services.command_center.system_services_command import system_services_config
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler


class SystemServicesOrchestrator:
    """
    Стандартизированный оркестратор для микросервиса SystemServices.
    Диспетчеризует команды на соответствующие обработчики и публикует результаты.
    Больше НЕ управляет транзакциями базы данных (это ответственность репозиториев).
    """
    def __init__(self, dependencies: Dict[str, Any]):
        self.dependencies = dependencies
        self.logger = dependencies.get('logger', logging.getLogger(__name__))
        self.message_bus: IMessageBus = dependencies.get('message_bus')
        # ИЗМЕНЕНО: db_session_factory больше не нужен оркестратору
        # self.db_session_factory: Type[AsyncSession] = dependencies.get('db_session_factory')
        # if not self.db_session_factory:
        #     self.logger.critical("Критическая ошибка: 'db_session_factory' не передан в зависимости оркестратора.")
        #     raise RuntimeError("'db_session_factory' is missing in orchestrator dependencies.")


        self.handlers: Dict[str, ISystemServiceHandler] = {
            command_name: info["handler"](dependencies=self.dependencies)
            for command_name, info in system_services_config.COMMAND_HANDLER_MAPPING.items()
        }
        self.logger.info(f"SystemServicesOrchestrator инициализирован с {len(self.handlers)} обработчиками.")

    async def process_command(self, validated_dto: BaseCommandDTO):
        """
        Главный метод-диспетчер. Получает DTO, находит обработчик и запускает его.
        Больше НЕ оборачивает выполнение обработчика в транзакцию базы данных.
        """
        command_type = validated_dto.command
        handler = self.handlers.get(command_type)
        if not handler:
            self.logger.error(f"Обработчик для команды '{command_type}' не найден.")
            error_result = BaseResultDTO(
                correlation_id=validated_dto.correlation_id,
                trace_id=validated_dto.trace_id,
                span_id=validated_dto.span_id,
                success=False,
                message=f"Обработчик для команды '{command_type}' не найден.",
                error=ErrorDetail(code="HANDLER_NOT_FOUND", message="Command handler not found."),
                client_id=validated_dto.client_id
            )
            await self._publish_response(error_result)
            return

        self.logger.info(f"Делегирование команды '{command_type}' обработчику...")
        result_dto: Optional[BaseResultDTO] = None 
        
        try:
            # Обработчик теперь не получает сессию напрямую, он будет использовать репозитории,
            # которые сами управляют своими сессиями и коммитами.
            result_dto = await handler.process(validated_dto)
            
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при обработке команды '{command_type}' (CorrID: {validated_dto.correlation_id}).")
            
            error_result = BaseResultDTO(
                correlation_id=validated_dto.correlation_id,
                trace_id=validated_dto.trace_id,
                span_id=validated_dto.span_id,
                success=False,
                message=f"Ошибка сервера при обработке команды '{command_type}': {e}",
                error=ErrorDetail(code="SERVER_ERROR", message=str(e)),
                client_id=validated_dto.client_id
            )
            result_dto = error_result

        finally:
            if result_dto:
                await self._publish_response(result_dto)

    async def _publish_response(self, result_dto: BaseResultDTO):
        """
        СТАНДАРТНЫЙ МЕТОД ОТПРАВКИ ОТВЕТА.
        Формирует WebSocketMessage и публикует его в Events.
        """
        client_id_for_delivery = getattr(result_dto, 'client_id', None)
        self.logger.info(f"SystemServicesOrchestrator: client_id_for_delivery перед публикацией: {client_id_for_delivery}")

        if not client_id_for_delivery:
            self.logger.warning(f"Результат для CorrID {result_dto.correlation_id} не может быть доставлен: отсутствует client_id.")
            return
        
        response_data_for_ws: Optional[Dict[str, Any]] = None
        if result_dto.data is not None:
            if isinstance(result_dto.data, list):
                response_data_for_ws = {"entities": [item.model_dump() for item in result_dto.data if isinstance(item, BaseModel)]}
            elif isinstance(result_dto.data, BaseModel):
                response_data_for_ws = result_dto.data.model_dump() # Это должно работать
            elif isinstance(result_dto.data, dict):
                response_data_for_ws = result_dto.data
            else:
                self.logger.warning(f"Неожиданный тип result_dto.data для WebSocketResponsePayload: {type(result_dto.data)}. Будет отправлен пустой словарь.")
                response_data_for_ws = {}

        response_payload = WebSocketResponsePayload(
            request_id=result_dto.correlation_id,
            status=ResponseStatus.SUCCESS if result_dto.success else ResponseStatus.FAILURE,
            message=result_dto.message,
            data=response_data_for_ws, # THIS is the data field of WebSocketResponsePayload
            error=result_dto.error
        )

        websocket_message = WebSocketMessage(
            type="RESPONSE",
            correlation_id=result_dto.correlation_id,
            trace_id=result_dto.trace_id,
            span_id=result_dto.span_id,
            client_id=client_id_for_delivery,
            payload=response_payload, # THIS is the payload field of WebSocketMessage
        )

        # НОВОЕ: Добавляем логирование полного JSON-сообщения перед публикацией
        full_message_to_publish = websocket_message.model_dump(mode='json')
        self.logger.critical(f"ДИАГНОСТИКА: Полное сообщение, отправляемое в RabbitMQ (Correlation ID: {result_dto.correlation_id}): {full_message_to_publish}")

        domain = getattr(result_dto, 'domain', 'system')
        action = getattr(result_dto, 'action', 'default')
        status_str = "success" if result_dto.success else "failure"
        routing_key = f"{RoutingKeys.RESPONSE_PREFIX}.{domain}.{action}.{status_str}"

        await self.message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=full_message_to_publish # Используем переменную с полным сообщением
        )
        self.logger.info(f"Ответ для CorrID {result_dto.correlation_id} опубликован в {Exchanges.EVENTS} с ключом '{routing_key}'.")
