# game_server/Logic/ApplicationLogic/shared_logic/ShardManagement/Handlers/assign_shard_handler.py

import logging
import datetime
import uuid
from typing import Dict, Any, Optional, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.contracts.dtos.shard.commands import NotifyAdminsCommandDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketSystemCommandToClientPayload # Добавлен AsyncSession

from .cleanup_inactive_players_handler import CleanupInactivePlayersHandler

# Импорты репозиториев и менеджеров
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus

# Импорты DTO и моделей


from .i_shard_management_handler import IShardManagementHandler
from .. import shard_helpers


async def _send_system_notification_to_gateway(
    message_bus: IMessageBus,
    notification_command_dto: NotifyAdminsCommandDTO,
    logger: logging.Logger,
    original_correlation_id: uuid.UUID,
    original_trace_id: uuid.UUID,
    original_span_id: Optional[uuid.UUID]
):
    system_command_payload = WebSocketSystemCommandToClientPayload(
        command_id=notification_command_dto.correlation_id,
        command_name=notification_command_dto.command,
        command_data={
            "reason": notification_command_dto.reason,
            "message": notification_command_dto.message,
            "timestamp": notification_command_dto.timestamp.isoformat()
        }
    )

    websocket_message = WebSocketMessage(
        type="SYSTEM_COMMAND",
        correlation_id=original_correlation_id,
        trace_id=original_trace_id,
        span_id=original_span_id,
        payload=system_command_payload,
        target_audience="ADMIN_PANEL",
        player_id=None
    )

    try:
        from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges
        routing_key = "system.notification.admins"
        await message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=websocket_message.model_dump(mode='json')
        )
        logger.info(f"Системное уведомление '{notification_command_dto.command}' (CmdID: {notification_command_dto.correlation_id}) отправлено администраторам. (Orig. Corr ID: {original_correlation_id})")
    except Exception as e:
        logger.error(f"Ошибка при отправке системного уведомления '{notification_command_dto.command}' (CmdID: {notification_command_dto.correlation_id}): {e}", exc_info=True)


class AssignShardHandler(IShardManagementHandler):
    """
    Обработчик, отвечающий за логику назначения игрока на шард.
    Теперь принимает сессию извне.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        # session_factory: Callable[[], AsyncSession], # УДАЛЕНО: Фабрика сессий больше не нужна здесь
        account_game_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository],
        game_shard_repo_factory: Callable[[AsyncSession], IGameShardRepository],
        message_bus: IMessageBus,
        cleanup_handler: CleanupInactivePlayersHandler,
    ):
        self.logger = logger
        # self._session_factory = session_factory # УДАЛЕНО
        self._account_game_data_repo_factory = account_game_data_repo_factory
        self._game_shard_repo_factory = game_shard_repo_factory
        self.message_bus = message_bus
        self.cleanup_handler = cleanup_handler
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(
        self,
        session: AsyncSession, # <--- ДОБАВЛЕНО: Теперь метод принимает активную сессию
        account_id: int,
        correlation_id: uuid.UUID,
        trace_id: uuid.UUID,
        span_id: Optional[uuid.UUID] = None,
    ) -> BaseResultDTO[Dict[str, Any]]:
        self.logger.info(f"Назначение шарда для account_id: {account_id} в рамках внешней транзакции. (Correlation ID: {correlation_id})")

        try:
            # Создаем экземпляры репозиториев с активной сессией, переданной извне
            account_game_data_repo = self._account_game_data_repo_factory(session)
            game_shard_repo = self._game_shard_repo_factory(session)

            best_shard_id_int = await shard_helpers.find_best_shard(
                account_game_data_repo,
                game_shard_repo,
            )
            
            if best_shard_id_int is None:
                self.logger.warning(f"Свободных шардов нет. Запуск цикла очистки неактивных игроков... (Correlation ID: {correlation_id})")
                
                # Передаем текущую сессию в cleanup_handler
                cleanup_report = await self.cleanup_handler.process(
                    session=session, # <--- ПЕРЕДАЕМ СЕССИЮ
                    correlation_id=correlation_id,
                    trace_id=trace_id,
                    span_id=uuid.uuid4(),
                    reason="NO_AVAILABLE_SHARDS"
                )
                
                if cleanup_report and cleanup_report.success and cleanup_report.data and cleanup_report.data.get('total_cleaned_count', 0) > 0:
                    self.logger.info(f"Очистка завершена. Освобождено мест: {cleanup_report.data.get('total_cleaned_count')}. Повторный поиск шарда... (Correlation ID: {correlation_id})")
                    best_shard_id_int = await shard_helpers.find_best_shard(
                        account_game_data_repo,
                        game_shard_repo,
                    )
                else:
                    self.logger.error(f"Очистка не освободила ни одного места. Все шарды переполнены активными игроками! (Correlation ID: {correlation_id})")
                    
                    notification_dto = NotifyAdminsCommandDTO(
                        command="system:notify_admins",
                        correlation_id=uuid.uuid4(),
                        trace_id=trace_id,
                        span_id=uuid.uuid4(),
                        reason="SHARDS_FULL",
                        message="Все шарды заполнены активными игроками. Требуется вмешательство для добавления новых мощностей."
                    )
                    
                    await _send_system_notification_to_gateway(
                        self.message_bus, notification_dto, self.logger,
                        original_correlation_id=correlation_id,
                        original_trace_id=trace_id,
                        original_span_id=span_id
                    )
            
            if best_shard_id_int:
                await game_shard_repo.increment_current_players(best_shard_id_int)
                
                await shard_helpers.finalize_assignment(
                    account_game_data_repo,
                    account_id, best_shard_id_int
                )
                self.logger.info(f"Игрок {account_id} успешно назначен на шард {best_shard_id_int}. (Correlation ID: {correlation_id})")
                
                # Коммит и откат управляются вызывающим кодом (DiscordHubHandler)
                self.logger.info(f"Операции назначения шарда для аккаунта {account_id} успешно выполнены. Коммит/откат управляется вызывающим.")

                return BaseResultDTO[Dict[str, Any]](
                    correlation_id=correlation_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    success=True,
                    message=f"Игрок назначен на шард {best_shard_id_int}.",
                    data={"shard_id": best_shard_id_int, "account_id": account_id, "is_new_assignment": True}
                )
            
            self.logger.warning(f"Не удалось назначить шард для игрока {account_id} даже после попытки очистки. (Correlation ID: {correlation_id})")
            
            # Откат будет выполнен внешним менеджером транзакций, если он есть
            # Здесь не нужен явный rollback, так как он будет сделан выше.

            return BaseResultDTO[Dict[str, Any]](
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                success=False,
                message="Не удалось назначить шард.",
                error=ErrorDetail(code="SHARD_ASSIGNMENT_FAILED_NO_SPACE", message="Нет свободных шардов после очистки.").model_dump()
            )
        
        except Exception as e:
            self.logger.exception(f"Непредвиденная ошибка при назначении шарда для account_id {account_id} (Correlation ID: {correlation_id})")
            # Откат будет выполнен внешним менеджером транзакций.
            # Здесь не нужен явный rollback.
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {str(e)}",
                error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(e)).model_dump()
            )