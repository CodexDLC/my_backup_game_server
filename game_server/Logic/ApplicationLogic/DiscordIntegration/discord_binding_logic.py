# game_server/Logic/ApplicationLogic/DiscordIntegration/discord_binding_logic.py

import logging
from typing import List, Dict, Any, Optional

# Импорт RepositoryManager для доступа к репозиториям PostgreSQL
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# Импортируем DTO-модели из common_contracts
from game_server.common_contracts.discord_integration.discord_commands_and_events import (
    DiscordEntityDTO,
    DiscordEntityCreateCommand,
    DiscordEntitiesSyncCommand,
    DiscordEntitiesDeleteCommand,
    DiscordSyncResultDTO
)


class DiscordBindingLogic:
    """
    Прикладная бизнес-логика для управления сущностями Discord на стороне БЭКЕНДА.
    Основная задача - взаимодействие с базой данных и кэшем через централизованные менеджеры.
    НЕ взаимодействует напрямую с Discord API.
    Теперь полностью оперирует Pydantic DTO-моделями.
    """
    def __init__(self, repository_manager: RepositoryManager, cache_managers: Dict[str, Any]):
        self.repository_manager = repository_manager
        self.discord_entity_repo = repository_manager.discord_entities # Использование RepositoryManager.
        self.cache_managers = cache_managers # Сохраняем доступ ко всем менеджерам кэша

        logger.info("✅ DiscordBindingLogic инициализирован.")

    async def sync_discord_entities_to_db(self, command: DiscordEntitiesSyncCommand) -> DiscordSyncResultDTO:
        """
        Принимает от бота команду для синхронизации сущностей Discord
        и синхронизирует их в базе данных.
        Создает новые записи или обновляет существующие.
        Принимает Pydantic DTO-модель и возвращает Pydantic DTO-модель.
        """
        created_count = 0
        updated_count = 0
        errors = []
        processed_entities_responses: List[DiscordEntityDTO] = []

        guild_id = command.guild_id
        entities_data = command.entities_data

        logger.info(f"Начало синхронизации Discord сущностей в БД для гильдии {guild_id}.")

        existing_db_entities = await self.discord_entity_repo.get_discord_entities_by_guild_id(guild_id)
        existing_by_discord_id = {entity.discord_id: entity for entity in existing_db_entities if entity.discord_id is not None}

        for item_command in entities_data:
            discord_id = item_command.discord_id
            name = item_command.name

            item_data_dict = item_command.model_dump(exclude_unset=True)

            if discord_id and discord_id in existing_by_discord_id:
                try:
                    updated_db_entity = await self.discord_entity_repo.update_discord_entity_by_discord_id(
                        guild_id=guild_id,
                        discord_id=discord_id,
                        updates=item_data_dict
                    )
                    if updated_db_entity:
                        updated_count += 1
                        processed_entities_responses.append(DiscordEntityDTO.model_validate(updated_db_entity.__dict__))
                    else:
                        errors.append({"discord_id": discord_id, "error": "Не удалось обновить сущность в БД."})
                except Exception as e:
                    errors.append({"discord_id": discord_id, "error": f"Ошибка при обновлении в БД: {e}"})
                    logger.error(f"Ошибка обновления в БД для Discord ID {discord_id}: {e}")
            else:
                try:
                    if discord_id is None:
                        errors.append({"name": name, "error": "Новая сущность не имеет Discord ID. Невозможно сохранить."})
                        logger.error(f"Попытка сохранить новую сущность '{name}' без Discord ID.")
                        continue

                    new_db_entity = await self.discord_entity_repo.create_discord_entity(item_data_dict)
                    created_count += 1
                    processed_entities_responses.append(DiscordEntityDTO.model_validate(new_db_entity.__dict__))
                except Exception as e:
                    errors.append({"name": name, "error": f"Ошибка при создании в БД: {e}"})
                    logger.error(f"Ошибка создания в БД для сущности '{name}': {e}")

        logger.info(f"Синхронизация БД завершена для гильдии {guild_id}. Создано: {created_count}, Обновлено: {updated_count}, Ошибок: {len(errors)}.")

        return DiscordSyncResultDTO(
            created_count=created_count,
            updated_count=updated_count,
            deleted_count=0,
            errors=errors,
            processed_entities=processed_entities_responses
        )

    async def delete_discord_entities_from_db(self, command: DiscordEntitiesDeleteCommand) -> Dict[str, Any]:
        """
        Удаляет сущности из базы данных по списку Discord ID и guild_id.
        Бот должен предварительно удалить их из Discord.
        Принимает Pydantic DTO-модель и возвращает стандартный Python-словарь.
        """
        guild_id = command.guild_id
        discord_ids = command.discord_ids

        logger.info(f"Начало удаления Discord сущностей из БД для гильдии {guild_id}, ID: {discord_ids}.")
        deleted_count = await self.discord_entity_repo.delete_discord_entities_batch(guild_id, discord_ids)
        logger.info(f"Удалено из БД: {deleted_count} записей для гильдии {guild_id}.")
        return {"deleted_count": deleted_count}

    async def create_single_discord_entity_in_db(self, command: DiscordEntityCreateCommand) -> DiscordEntityDTO:
        """
        Создает одну сущность Discord в базе данных.
        Принимает Pydantic DTO-модель и возвращает Pydantic DTO-модель.
        """
        discord_id = command.discord_id
        name = command.name
        guild_id = command.guild_id

        if discord_id is None:
            logger.error(f"Попытка создать одиночную сущность '{name}' без Discord ID.")
            raise ValueError("Для создания сущности в БД требуется Discord ID.")

        logger.info(f"Попытка создать одиночную Discord сущность в БД: '{name}' (Discord ID: {discord_id}).")

        existing_entity = await self.discord_entity_repo.get_discord_entity_by_discord_id(
            guild_id=guild_id,
            discord_id=discord_id
        )
        if existing_entity:
            logger.warning(f"Сущность с Discord ID {discord_id} уже существует в БД. Возвращаем существующую.")
            return DiscordEntityDTO.model_validate(existing_entity.__dict__)

        new_db_entity = await self.discord_entity_repo.create_discord_entity(command.model_dump(exclude_unset=True))
        logger.info(f"Одиночная сущность '{name}' (Discord ID: {new_db_entity.discord_id}) успешно создана в БД.")
        return DiscordEntityDTO.model_validate(new_db_entity.__dict__)

    async def get_discord_entities_from_db(self, guild_id: int) -> List[DiscordEntityDTO]:
        """
        Получает все сущности Discord для указанного ID гильдии из базы данных.
        Возвращает список Pydantic DTO-моделей.
        """
        logger.info(f"Запрос на получение всех Discord сущностей из БД для гильдии {guild_id}.")
        db_entities = await self.discord_entity_repo.get_discord_entities_by_guild_id(guild_id)
        response_entities = [DiscordEntityDTO.model_validate(entity.__dict__) for entity in db_entities]
        logger.info(f"Найдено {len(response_entities)} сущностей для гильдии {guild_id}.")
        return response_entities