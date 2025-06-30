# game_server/Logic/ApplicationLogic/SystemServices/handler/discord/create_single_entity_handler.py

from typing import Dict, Any


from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

# 🔥 ИЗМЕНЕНИЕ: Импортируем новые стандартизированные DTO
from game_server.common_contracts.dtos.discord_dtos import DiscordEntityCreateCommand, DiscordEntityDTO # DiscordEntityCreateResultDTO будет заменен
from game_server.common_contracts.dtos.base_dtos import BaseResultDTO # Базовый класс для всех результатов
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler

class CreateSingleEntityHandler(ISystemServiceHandler):
    """
    Обработчик для создания одной единственной сущности Discord в БД.
    Предотвращает создание дубликатов.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            self.repo_manager: RepositoryManager = self.dependencies['repository_manager']
            self.discord_entity_repo = self.repo_manager.discord_entities
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

    # 🔥 ИЗМЕНЕНИЕ: Возвращаемый тип теперь BaseResultDTO[DiscordEntityDTO]
    async def process(self, command_dto: DiscordEntityCreateCommand) -> BaseResultDTO[DiscordEntityDTO]:
        guild_id = command_dto.guild_id
        discord_id = command_dto.discord_id

        self.logger.info(f"Получена команда '{command_dto.command}' для сущности с Discord ID: {discord_id} (Correlation ID: {command_dto.correlation_id})")

        try:
            # Сначала проверим, не существует ли уже такая сущность
            existing_entity = await self.discord_entity_repo.get_discord_entity_by_discord_id(
                guild_id=guild_id,
                discord_id=discord_id
            )

            if existing_entity:
                self.logger.warning(f"Сущность с Discord ID {discord_id} уже существует в БД. Возвращаем существующую. (Correlation ID: {command_dto.correlation_id})")
                # 🔥 ИЗМЕНЕНИЕ: Возвращаем BaseResultDTO
                return BaseResultDTO[DiscordEntityDTO](
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id, # Пропагируем trace_id
                    span_id=command_dto.span_id,   # Пропагируем span_id
                    success=True,
                    message="Сущность уже существует, новая не создавалась.",
                    data=DiscordEntityDTO.model_validate(existing_entity.__dict__) # Данные в поле 'data'
                )

            # Если не существует, создаем новую
            # exclude={'command', 'correlation_id', 'trace_id', 'span_id', 'timestamp'}
            new_entity_data = command_dto.model_dump(exclude={field.name for field in command_dto.model_fields.values() if field.json_schema_extra and field.json_schema_extra.get('exclude_from_payload')}) # Исключаем поля BaseCommandDTO
            new_db_entity = await self.discord_entity_repo.create_discord_entity(new_entity_data)

            self.logger.info(f"Сущность '{new_db_entity.name}' (Discord ID: {new_db_entity.discord_id}) успешно создана. (Correlation ID: {command_dto.correlation_id})")

            # 🔥 ИЗМЕНЕНИЕ: Возвращаем BaseResultDTO
            return BaseResultDTO[DiscordEntityDTO](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id, # Пропагируем trace_id
                span_id=command_dto.span_id,   # Пропагируем span_id
                success=True,
                message="Сущность успешно создана.",
                data=DiscordEntityDTO.model_validate(new_db_entity.__dict__) # Данные в поле 'data'
            )

        except Exception as e:
            self.logger.exception(f"Критическая ошибка при создании сущности с Discord ID {discord_id} (Correlation ID: {command_dto.correlation_id}): {e}")
            # 🔥 ИЗМЕНЕНИЕ: Возвращаем BaseResultDTO
            return BaseResultDTO[DiscordEntityDTO](
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id, # Пропагируем trace_id
                span_id=command_dto.span_id,   # Пропагируем span_id
                success=False,
                message=f"Критическая ошибка на сервере: {e}",
                data=None # Данные отсутствуют при ошибке
            )