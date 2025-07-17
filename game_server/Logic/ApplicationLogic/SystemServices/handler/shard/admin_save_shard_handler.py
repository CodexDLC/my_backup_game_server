# game_server/Logic/ApplicationLogic/SystemServices/handler/shard/admin_save_shard_handler.py

import logging
from typing import Dict, Any, Callable
import inject
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

# 👇 ИЗМЕНЕНИЕ: Импортируем декоратор и фабрику напрямую
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импортируем интерфейс репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository


from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.contracts.dtos.shard.commands import SaveShardCommandDTO
from game_server.contracts.dtos.shard.results import ShardOperationResultDTO


class AdminSaveShardHandler(ISystemServiceHandler):
    """
    Обработчик для сохранения (создания или обновления) данных игрового шарда.
    Теперь использует декоратор @transactional.
    """
    # 👇 ИЗМЕНЕНИЕ: Убираем session_factory из __init__
    @inject.autoparams('logger', 'game_shards_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 game_shards_repo_factory: Callable[[AsyncSession], IGameShardRepository]
                 ):
        self._logger = logger
        self._game_shards_repo_factory = game_shards_repo_factory
        self._logger.info("AdminSaveShardHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    # 👇 ИЗМЕНЕНИЕ: Оборачиваем метод в декоратор и убираем ручное управление транзакцией
    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: SaveShardCommandDTO) -> ShardOperationResultDTO:
        self.logger.info(f"Получена команда '{command_dto.command}' для шарда '{command_dto.shard_name}'.")

        # Создаем репозиторий с активной сессией, переданной декоратором
        game_shards_repo = self._game_shards_repo_factory(session)
        
        try:
            shard_data_to_save = command_dto.model_dump(exclude={
                "command", "correlation_id", "version", "timestamp", "trace_id", "span_id", "client_id", "payload"
            })
            
            saved_shard = await game_shards_repo.upsert_shard(shard_data_to_save)

            self.logger.info(f"Шард '{saved_shard.shard_name}' успешно сохранен. Транзакция будет закоммичена.")

            return ShardOperationResultDTO(
                correlation_id=command_dto.correlation_id,
                success=True,
                message=f"Шард '{saved_shard.shard_name}' успешно сохранен.",
                shard_data=saved_shard.to_dict(),
                client_id=command_dto.client_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id
            )
        except Exception as e:
            # Логируем ошибку. Откат транзакции произойдет автоматически в декораторе.
            self.logger.exception(f"Ошибка при обработке команды сохранения шарда: {e}")
            # Перевыбрасываем исключение, чтобы декоратор его поймал и сделал rollback
            raise