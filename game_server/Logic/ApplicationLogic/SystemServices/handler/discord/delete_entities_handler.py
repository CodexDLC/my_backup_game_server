# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/delete_entities_handler.py

import logging
from typing import Dict, Any, List, Callable
import inject
from sqlalchemy.ext.asyncio import AsyncSession

# 👇 ИЗМЕНЕНИЕ: Импортируем фабрику сессий и декоратор
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импортируем интерфейс репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntityBatchDeleteRequest
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO


class DeleteDiscordEntitiesHandler(ISystemServiceHandler):
    """
    Обработчик для массового удаления сущностей Discord из БД. Работает в рамках транзакции.
    """
    # 👇 ИЗМЕНЕНИЕ: Внедряем логгер и фабрику репозитория
    @inject.autoparams('logger', 'discord_repo_factory')
    def __init__(self,
                 logger: logging.Logger,
                 discord_repo_factory: Callable[[AsyncSession], IDiscordEntityRepository]
                 ):
        self._logger = logger
        self._discord_repo_factory = discord_repo_factory
        self._logger.info("DeleteDiscordEntitiesHandler инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    # 👇 ИЗМЕНЕНИЕ: Делаем метод транзакционным
    @transactional(AsyncSessionLocal)
    async def process(self, session: AsyncSession, command_dto: UnifiedEntityBatchDeleteRequest) -> BaseResultDTO[Dict[str, Any]]:
        guild_id = command_dto.guild_id
        discord_ids = command_dto.discord_ids
        
        self.logger.info(f"Получена команда '{command_dto.command}' для гильдии {guild_id}. Удаление {len(discord_ids)} сущностей.")

        # Создаем репозиторий с активной сессией
        discord_entity_repo = self._discord_repo_factory(session)

        try:
            # ПРИМЕЧАНИЕ: Для большей производительности здесь лучше использовать один batch-метод,
            # например, discord_entity_repo.delete_discord_entities_batch(discord_ids)
            deleted_count = 0
            for discord_id in discord_ids:
                try:
                    success = await discord_entity_repo.delete_discord_entity_by_id(discord_id)
                    if success:
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Ошибка при удалении сущности Discord ID {discord_id}: {e}")
            
            self.logger.info(f"Успешно удалено {deleted_count} сущностей для гильдии {guild_id}.")

            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                success=True,
                message=f"Успешно удалено {deleted_count} из {len(discord_ids)} запрошенных сущностей.",
                data={"deleted_count": deleted_count},
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.exception(f"Критическая ошибка при массовом удалении сущностей для гильдии {guild_id}: {e}")
            return BaseResultDTO[Dict[str, Any]](
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data={"deleted_count": 0, "error": str(e)},
                client_id=command_dto.client_id
            )