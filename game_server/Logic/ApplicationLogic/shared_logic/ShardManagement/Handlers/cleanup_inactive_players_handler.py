# game_server/Logic/ApplicationLogic/shared_logic/ShardManagement/Handlers/cleanup_inactive_players_handler.py

import logging
import datetime
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
import uuid
import inject
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail # Добавлен AsyncSession

from .i_shard_management_handler import IShardManagementHandler

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count.shard_count_cache_manager import ShardCountCacheManager
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository



INACTIVITY_THRESHOLD = datetime.timedelta(hours=24)

class CleanupInactivePlayersHandler(IShardManagementHandler):
    """
    Обработчик, отвечающий за очистку "прописки" у неактивных игроков для освобождения слотов.
    Теперь принимает сессию извне.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        # session_factory: Callable[[], AsyncSession], # УДАЛЕНО: Фабрика сессий больше не нужна здесь
        account_game_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository],
        game_shard_repo_factory: Callable[[AsyncSession], IGameShardRepository],
        shard_count_cache_manager: ShardCountCacheManager,
    ):
        self.logger = logger
        # self._session_factory = session_factory # УДАЛЕНО
        self._account_game_data_repo_factory = account_game_data_repo_factory
        self._game_shard_repo_factory = game_shard_repo_factory
        self.shard_count_cache_manager = shard_count_cache_manager
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(
        self,
        session: AsyncSession, # <--- ДОБАВЛЕНО: Теперь метод принимает активную сессию
        correlation_id: uuid.UUID,
        trace_id: uuid.UUID,
        span_id: Optional[uuid.UUID] = None,
        reason: str = "UNKNOWN"
    ) -> BaseResultDTO[Dict[str, Any]]:
        self.logger.info(f"Запуск процесса очистки неактивных игроков. Причина: {reason} (CorrID: {correlation_id}) в рамках внешней транзакции.")
        
        cleaned_report = defaultdict(int)

        try:
            # Создаем экземпляры репозиториев с активной сессией, переданной извне
            account_game_data_repo = self._account_game_data_repo_factory(session)
            game_shard_repo = self._game_shard_repo_factory(session)

            threshold_date = datetime.datetime.now(datetime.timezone.utc) - INACTIVITY_THRESHOLD
            
            inactive_players = await account_game_data_repo.get_inactive_accounts_with_shard_id(
                days_inactive=int(INACTIVITY_THRESHOLD.total_seconds() / 86400)
            )

            if not inactive_players:
                self.logger.info("Неактивные игроки для очистки не найдены.")
                # Коммит и откат управляются вызывающим кодом.
                return BaseResultDTO(
                    correlation_id=correlation_id, trace_id=trace_id, span_id=span_id,
                    success=True, message="Неактивные игроки не найдены.",
                    data={'total_cleaned_count': 0, 'shards_impacted': {}}
                )

            player_ids_to_clear = []
            for player in inactive_players:
                if player.shard_id:
                    cleaned_report[str(player.shard_id)] += 1
                player_ids_to_clear.append(player.account_id)

            self.logger.info(f"Найдено {len(player_ids_to_clear)} неактивных игроков на {len(cleaned_report)} шардах для очистки.")

            await account_game_data_repo.clear_shard_id_for_accounts(player_ids_to_clear)

            for shard_id, count in cleaned_report.items():
                await game_shard_repo.decrement_current_players(int(shard_id), count)
                self.logger.info(f"Освобождено {count} слотов на шарде {shard_id}.")

            total_cleaned_count = sum(cleaned_report.values())
            self.logger.info(f"Процесс очистки неактивных игроков успешно завершен. Всего освобождено: {total_cleaned_count}.")
            
            # Коммит и откат управляются вызывающим кодом.
            self.logger.info(f"Операции очистки успешно выполнены. Коммит/откат управляется вызывающим.")

            return BaseResultDTO(
                correlation_id=correlation_id, trace_id=trace_id, span_id=span_id,
                success=True, message=f"Очищено {total_cleaned_count} неактивных игроков.",
                data={'total_cleaned_count': total_cleaned_count, 'shards_impacted': dict(cleaned_report)}
            )

        except SQLAlchemyError as e:
            # Откат будет выполнен внешним менеджером транзакций.
            self.logger.error(f"Ошибка базы данных во время очистки игроков: {e}", exc_info=True)
            return BaseResultDTO(
                correlation_id=correlation_id, trace_id=trace_id, span_id=span_id,
                success=False, message=f"Ошибка БД при очистке: {str(e)}",
                error=ErrorDetail(code="DB_ERROR_CLEANUP", message=str(e)).model_dump()
            )
        except Exception as e:
            # Откат будет выполнен внешним менеджером транзакций.
            self.logger.exception(f"Непредвиденная ошибка во время очистки игроков: {e}")
            return BaseResultDTO(
                correlation_id=correlation_id, trace_id=trace_id, span_id=span_id,
                success=False, message=f"Внутренняя ошибка при очистке: {str(e)}",
                error=ErrorDetail(code="INTERNAL_ERROR_CLEANUP", message=str(e)).model_dump()
            )