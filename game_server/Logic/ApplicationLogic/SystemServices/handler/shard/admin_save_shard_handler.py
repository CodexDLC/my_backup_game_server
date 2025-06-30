# game_server/Logic/ApplicationLogic/SystemServices/handler/shard/admin_save_shard_handler.py

import logging
from typing import Dict, Any
from sqlalchemy.exc import SQLAlchemyError

from game_server.common_contracts.dtos.shard_dtos import SaveShardCommandDTO, ShardOperationResultDTO
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.config.logging.logging_setup import app_logger as logger


class AdminSaveShardHandler(ISystemServiceHandler):
    """
    Обработчик для сохранения (создания или обновления) данных игрового шарда.
    Теперь обрабатывает команду 'system:save_shard'.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.shard_repo = self.repo_manager.game_shards
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    async def process(self, command_dto: SaveShardCommandDTO) -> ShardOperationResultDTO:
        """
        Выполняет логику Upsert для шарда.
        """
        # 🔥 ИЗМЕНЕНИЕ: Обновлен лог, чтобы отражать новое имя команды
        self.logger.info(f"Получена команда '{command_dto.command}' (system:save_shard) для шарда '{command_dto.shard_name}' (Guild ID: {command_dto.discord_guild_id}, CorrID: {command_dto.correlation_id})")
        self.logger.info(f"AdminSaveShardHandler: Client ID из command_dto: {command_dto.client_id}")

        try:
            shard_data_to_save = command_dto.model_dump(exclude={
                "command", "correlation_id", "version", "timestamp", "trace_id", "span_id", "client_id", "payload"
            }, by_alias=False)
            
            saved_shard = await self.shard_repo.upsert_shard(shard_data_to_save)

            return ShardOperationResultDTO(
                correlation_id=command_dto.correlation_id,
                success=True,
                message=f"Шард '{saved_shard.shard_name}' успешно сохранен.",
                shard_data=saved_shard.to_dict() if hasattr(saved_shard, 'to_dict') else saved_shard,
                client_id=command_dto.client_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id
            )

        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка базы данных при сохранении шарда {command_dto.discord_guild_id}: {e}", exc_info=True)
            return ShardOperationResultDTO(
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Внутренняя ошибка базы данных: {e}",
                shard_data=None,
                client_id=command_dto.client_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id
            )
        except Exception as e:
            self.logger.exception(f"Непредвиденная ошибка при обработке команды сохранения шарда: {e}")
            return ShardOperationResultDTO(
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Непредвиденная внутренняя ошибка: {e}",
                shard_data=None,
                client_id=command_dto.client_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id
            )
