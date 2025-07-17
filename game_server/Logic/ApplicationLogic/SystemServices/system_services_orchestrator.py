# game_server/Logic/ApplicationLogic/SystemServices/system_services_orchestrator.py
# Version: 0.007 # Увеличиваем версию для учета изменений в обработчиках и транзакциях

import logging
from typing import Dict, Any, Optional, Type, Callable # Добавлен Callable
from pydantic import BaseModel

from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.contracts.shared_models.base_responses import ErrorDetail, ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload
from game_server.game_services.command_center.system_services_command import system_services_config
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler



import inject

class SystemServicesOrchestrator:
    """
    Стандартизированный оркестратор для микросервиса SystemServices.
    Диспетчеризует команды на соответствующие обработчики.
    Управление транзакциями делегируется самим обработчикам (через @transactional).
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        message_bus: IMessageBus,
        # 🔥 УДАЛЕНО: session_factory не нужен в оркестраторе
    ):
        self.logger = logger
        self.message_bus = message_bus
        # self._session_factory = session_factory # 🔥 УДАЛЕНО

        self.handlers: Dict[str, ISystemServiceHandler] = {
            command_name: inject.instance(info["handler"])
            for command_name, info in system_services_config.COMMAND_HANDLER_MAPPING.items()
        }
        self.logger.info(f"SystemServicesOrchestrator инициализирован с {len(self.handlers)} обработчиками.")

    async def process_command(self, validated_dto: BaseCommandDTO):
        """
        Главный метод-диспетчер. Получает DTO, находит обработчик и запускает его.
        Транзакция управляется самим обработчиком (через @transactional).
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

        self.logger.info(f"Делегирование команды '{command_type}' обработчику (CorrID: {validated_dto.correlation_id}).")
        
        result_dto: Optional[BaseResultDTO] = None 
        
        # 🔥 ИЗМЕНЕНО: Просто вызываем process обработчика.
        # Декоратор @transactional на методе process обработчика позаботится о сессии и транзакции.
        try:
            result_dto = await handler.process(command_dto=validated_dto) # <--- Вызываем без явной сессии
            self.logger.info(f"Команда '{command_type}' успешно обработана. Результат: {'Успех' if result_dto.success else 'Ошибка'}.")
            
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
                response_data_for_ws = result_dto.data.model_dump()
            elif isinstance(result_dto.data, dict):
                response_data_for_ws = result_dto.data
            else:
                self.logger.warning(f"Неожиданный тип result_dto.data для WebSocketResponsePayload: {type(result_dto.data)}. Будет отправлен пустой словарь.")
                response_data_for_ws = {}

        response_payload = WebSocketResponsePayload(
            request_id=result_dto.correlation_id,
            status=ResponseStatus.SUCCESS if result_dto.success else ResponseStatus.FAILURE,
            message=result_dto.message,
            data=response_data_for_ws,
            error=result_dto.error
        )
        self.logger.debug(f"DEBUG: SystemServicesOrchestrator: Сформирован response_payload: {response_payload.model_dump_json()}")

        websocket_message = WebSocketMessage(
            type="RESPONSE",
            correlation_id=result_dto.correlation_id,
            trace_id=result_dto.trace_id,
            span_id=result_dto.span_id,
            client_id=client_id_for_delivery,
            payload=response_payload,
        )
        self.logger.debug(f"DEBUG: SystemServicesOrchestrator: Сформирован websocket_message: {websocket_message.model_dump_json()}")

        full_message_to_publish = websocket_message.model_dump(mode='json')
        self.logger.debug(f"DEBUG: SystemServicesOrchestrator: Полное сообщение для публикации (JSON): {full_message_to_publish}")


        domain = getattr(result_dto, 'domain', 'system')
        action = getattr(result_dto, 'action', 'default')
        status_str = "success" if result_dto.success else "failure"
        routing_key = f"{RoutingKeys.RESPONSE_PREFIX}.{domain}.{action}.{status_str}"

        self.logger.debug(f"DEBUG: SystemServicesOrchestrator: Публикация в exchange '{Exchanges.EVENTS}' с routing_key '{routing_key}'.")
        await self.message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=full_message_to_publish
        )
        self.logger.info(f"Ответ для CorrID {result_dto.correlation_id} опубликован в {Exchanges.EVENTS} с ключом '{routing_key}'.")