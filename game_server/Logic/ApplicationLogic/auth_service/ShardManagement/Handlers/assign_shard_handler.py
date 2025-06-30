# game_server\Logic\ApplicationLogic\auth_service\ShardManagement\Handlers\assign_shard_handler.py

import logging
import datetime
import uuid # Добавлен для UUID
from typing import Dict, Any, Optional

# 🔥 ИЗМЕНЕНИЕ: Импортируем новые стандартизированные DTO и WebSocket-модели
from game_server.common_contracts.dtos.shard_dtos import NotifyAdminsCommandDTO
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO, BaseCommandDTO
from game_server.common_contracts.shared_models.api_contracts import ErrorDetail, WebSocketMessage, WebSocketSystemCommandToClientPayload


from .i_shard_management_handler import IShardManagementHandler
from .. import shard_helpers
from .cleanup_inactive_players_handler import CleanupInactivePlayersHandler

# Утилиты для отправки сообщений
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges


# 🔥 ИЗМЕНЕНИЕ: Вспомогательная функция для отправки системных уведомлений через WebSocketMessage
async def _send_system_notification_to_gateway(
    message_bus: RabbitMQMessageBus,
    notification_command_dto: NotifyAdminsCommandDTO, # Теперь это NotifyAdminsCommandDTO
    logger: logging.Logger,
    original_correlation_id: uuid.UUID, # Оригинальный correlation_id от запроса игрока/клиента
    original_trace_id: uuid.UUID,      # Оригинальный trace_id
    original_span_id: Optional[uuid.UUID] # Оригинальный span_id
):
    """
    Формирует и отправляет WebSocketMessage с WebSocketSystemCommandToClientPayload
    в Gateway для системных уведомлений.
    """
    # 🔥 ИЗМЕНЕНИЕ: Формируем WebSocketSystemCommandToClientPayload
    system_command_payload = WebSocketSystemCommandToClientPayload(
        command_id=notification_command_dto.correlation_id, # command_id для системной команды
        command_name=notification_command_dto.command,       # Имя команды (например, "system:notify_admins")
        command_data={
            "reason": notification_command_dto.reason,
            "message": notification_command_dto.message,
            "timestamp": notification_command_dto.timestamp.isoformat()
        }
    )

    # 🔥 ИЗМЕНЕНИЕ: Создаем WebSocketMessage для системной команды
    websocket_message = WebSocketMessage(
        type="SYSTEM_COMMAND", # Тип сообщения
        correlation_id=original_correlation_id, # Связываем с оригинальным запросом, если есть
        trace_id=original_trace_id,
        span_id=original_span_id,
        payload=system_command_payload,
        target_audience="ADMIN_PANEL", # Или "DISCORD_BOT", или "ALL" в зависимости от того, кому адресовано уведомление
        player_id=None # Это системная команда, не привязана к конкретному player_id
    )

    try:
        # Отправляем через Exchanges.EVENTS, чтобы Gateway подхватил
        routing_key = "system.notification.admins" # Специфический routing key для админских уведомлений
        
        await message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=websocket_message.model_dump(mode='json') # Публикуем как Python dict (будет упакован в MsgPack)
        )
        logger.info(f"Системное уведомление '{notification_command_dto.command}' (CmdID: {notification_command_dto.correlation_id}) отправлено администраторам. (Orig. Corr ID: {original_correlation_id})")
    except Exception as e:
        logger.error(f"Ошибка при отправке системного уведомления '{notification_command_dto.command}' (CmdID: {notification_command_dto.correlation_id}): {e}", exc_info=True)


class AssignShardHandler(IShardManagementHandler):
    """
    Обработчик, отвечающий за логику назначения игрока на шард.
    Включает механизм очистки неактивных игроков при нехватке мест.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager = self.dependencies['repository_manager']
            self.shard_count_manager = self.dependencies['shard_count_manager']
            self.message_bus: RabbitMQMessageBus = self.dependencies['message_bus']
            self.cleanup_handler = CleanupInactivePlayersHandler(dependencies)
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    # 🔥 ИЗМЕНЕНИЕ: Метод process теперь принимает correlation_id, trace_id, span_id
    async def process(
        self,
        account_id: int,
        correlation_id: uuid.UUID, # Из BaseRequest/BaseCommandDTO
        trace_id: uuid.UUID,       # Из BaseRequest/BaseCommandDTO
        span_id: Optional[uuid.UUID] = None, # Из BaseRequest/BaseCommandDTO
        preferred_shard_id: str | None = None
    ) -> BaseResultDTO[Dict[str, Any]]: # 🔥 Возвращаем BaseResultDTO
        """
        Основной метод, координирующий назначение шарда.
        """
        self.logger.info(f"Назначение шарда для account_id: {account_id}. Preferred: {preferred_shard_id}. (Correlation ID: {correlation_id})")

        # Шаг 1: Проверить существующую "прописку"
        game_data = await self.repo_manager.account_game_data.get_by_account_id(account_id)
        if game_data and game_data.shard_id:
            self.logger.info(f"Аккаунт {account_id} уже привязан к шарду {game_data.shard_id}. (Correlation ID: {correlation_id})")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                success=True,
                message=f"Игрок уже привязан к шарду {game_data.shard_id}.",
                data={"shard_id": game_data.shard_id, "account_id": account_id, "is_new_assignment": False}
            )

        # Шаг 2: Попытка №1 - Поиск лучшего шарда
        best_shard_id = await shard_helpers.find_best_shard(
            self.repo_manager, self.shard_count_manager, preferred_shard_id
        )
        
        # Шаг 3: Если свободных шардов нет, запускаем очистку
        if not best_shard_id:
            self.logger.warning(f"Свободных шардов нет. Запуск цикла очистки неактивных игроков... (Correlation ID: {correlation_id})")
            cleanup_report = await self.cleanup_handler.process(
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=uuid.uuid4(), # Новый span для операции очистки
                reason="NO_AVAILABLE_SHARDS" # Добавляем причину
            )
            
            # Шаг 4: Анализ результата очистки
            if cleanup_report and cleanup_report.data and cleanup_report.data.get('total_cleaned_count', 0) > 0:
                self.logger.info(f"Очистка завершена. Освобождено мест: {cleanup_report.data.get('total_cleaned_count')}. Повторный поиск шарда... (Correlation ID: {correlation_id})")
                best_shard_id = await shard_helpers.find_best_shard(
                    self.repo_manager, self.shard_count_manager, preferred_shard_id=None
                )
            else:
                self.logger.error(f"Очистка не освободила ни одного места. Все шарды переполнены активными игроками! (Correlation ID: {correlation_id})")
                
                # Создаем DTO для уведомления админов
                notification_dto = NotifyAdminsCommandDTO(
                    command="system:notify_admins_shards_full",
                    correlation_id=uuid.uuid4(), # Свой correlation_id для этой системной команды
                    trace_id=trace_id,          # Связываем с родительской трассировкой
                    span_id=uuid.uuid4(),       # Новый span для уведомления
                    reason="SHARDS_FULL",
                    message="Все шарды заполнены активными игроками. Требуется вмешательство для добавления новых мощностей."
                )
                
                # Отправляем уведомление через новую вспомогательную функцию
                await _send_system_notification_to_gateway(
                    self.message_bus, notification_dto, self.logger,
                    original_correlation_id=correlation_id,
                    original_trace_id=trace_id,
                    original_span_id=span_id
                )
        
        # Шаг 5: Финализация или возврат ошибки
        if best_shard_id:
            await shard_helpers.finalize_assignment(
                self.repo_manager, self.shard_count_manager, account_id, best_shard_id
            )
            self.logger.info(f"Игрок {account_id} успешно назначен на шард {best_shard_id}. (Correlation ID: {correlation_id})")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                success=True,
                message=f"Игрок назначен на шард {best_shard_id}.",
                data={"shard_id": best_shard_id, "account_id": account_id, "is_new_assignment": True}
            )
        
        self.logger.warning(f"Не удалось назначить шард для игрока {account_id} даже после попытки очистки. (Correlation ID: {correlation_id})")
        return BaseResultDTO[Dict[str, Any]](
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            success=False,
            message="Не удалось назначить шард.",
            error=ErrorDetail(code="SHARD_ASSIGNMENT_FAILED_NO_SPACE", message="Нет свободных шардов после очистки.") # Добавляем ErrorDetail
        )