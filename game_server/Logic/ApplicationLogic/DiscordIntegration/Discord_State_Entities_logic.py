import uuid # Оставляем на случай, если где-то еще может понадобиться или для отладки
from typing import Dict, Any, List, Optional

# Импорт RepositoryManager для доступа к репозиториям PostgreSQL
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

# Импорт get_initialized_app_cache_managers для доступа к кэш-менеджерам (если потребуются)
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import get_initialized_app_cache_managers

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# Импортируем DTO-модели из common_contracts
from game_server.common_contracts.discord_integration.discord_commands_and_events import (
    StateEntityDiscordDTO,
    StateEntityDiscordCreateUpdateCommand,
    StateEntityDiscordUpdateCommand,
    StateEntityDiscordDeleteCommand,
    StateEntitiesDiscordBatchCreateCommand
)

# --- Добавляем специфические исключения ---
class EntityNotFoundException(Exception):
    """Исключение, выбрасываемое, когда запрошенная сущность Discord не найдена."""
    pass

class InvalidUUIDError(ValueError): # Это исключение теперь, вероятно, не нужно, но оставим пока
    """Исключение, выбрасываемое при некорректном формате UUID."""
    pass
# ----------------------------------------

class StateEntitiesDiscordLogic:
    """
    Прикладная бизнес-логика для обработки операций со StateEntitiesDiscord.
    Сессии базы данных и кэш-менеджеры внедряются через конструктор (через RepositoryManager и Cache Managers).
    Оперирует Pydantic DTO-моделями.
    Первичный ключ для StateEntityDiscord: (guild_id, discord_role_id)
    """

    def __init__(self, repository_manager: RepositoryManager, cache_managers: Dict[str, Any]):
        self.repository_manager = repository_manager
        # Используем репозиторий для Discord ролей из RepositoryManager
        # ВАЖНО: Предполагается, что методы этого репозитория (DiscordRolesMappingRepositoryImpl)
        # были обновлены для использования (guild_id, discord_role_id) в качестве ПК.
        self.discord_roles_mapping_repo = repository_manager.discord_roles_mapping
        self.cache_managers = cache_managers

        logger.info("✅ StateEntitiesDiscordLogic инициализирован.")

    # Сигнатура не меняется, но внутренняя логика репозитория теперь использует другой ПК
    async def get_all_entities_for_guild(self, guild_id: int) -> List[StateEntityDiscordDTO]:
        try:
            # Репозиторий возвращает ORM-объекты
            # Предполагается, что get_all_roles_for_guild возвращает объекты с access_code как атрибутом
            entities = await self.discord_roles_mapping_repo.get_all_roles_for_guild(guild_id)
            if not entities:
                logger.info(f"Нет сущностей для гильдии {guild_id}.")
                return [] # Возвращаем пустой список DTO

            # Преобразуем ORM-объекты в DTO-модели
            return [StateEntityDiscordDTO.model_validate(e.__dict__) for e in entities]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении всех сущностей для гильдии {guild_id}: {e}", exc_info=True)
            raise

    # Изменена сигнатура: принимает guild_id и discord_role_id как ПК
    async def get_entity_by_primary_key(self, guild_id: int, discord_role_id: int) -> StateEntityDiscordDTO: # Изменено
        try:
            # Репозиторий возвращает ORM-объект.
            # ВАЖНО: Предполагается, что get_role_by_pk теперь принимает (guild_id, discord_role_id)
            entity = await self.discord_roles_mapping_repo.get_role_by_pk(guild_id, discord_role_id) # Изменено
            if entity is None:
                logger.info(f"Сущность не найдена по ПК (Guild: {guild_id}, Role: {discord_role_id})")
                raise EntityNotFoundException(f"Сущность с Guild ID {guild_id}, Role ID {discord_role_id} не найдена.")

            # Преобразуем ORM-объект в DTO
            return StateEntityDiscordDTO.model_validate(entity.__dict__)
        except Exception as e:
            logger.error(f"❌ Ошибка при получении сущности по ПК (Guild: {guild_id}, Role: {discord_role_id}): {e}", exc_info=True)
            raise

    # Изменена сигнатура: принимает StateEntityDiscordUpdateCommand (ПК в DTO)
    async def update_entity_by_primary_key(self, command: StateEntityDiscordUpdateCommand) -> StateEntityDiscordDTO: # Изменено
        guild_id = command.guild_id
        discord_role_id = command.discord_role_id
        # Обновления теперь берутся напрямую из полей DTO
        updates_dict = command.model_dump(include={'access_code', 'description'}, exclude_unset=True) # Только изменяемые поля

        try:
            # ВАЖНО: Предполагается, что update_role_by_pk теперь принимает (guild_id, discord_role_id) как ПК
            # и словарь обновлений.
            updated_entity = await self.discord_roles_mapping_repo.update_role_by_pk(
                guild_id, discord_role_id, updates_dict # Изменено
            )
            if updated_entity is None:
                logger.info(f"Сущность не найдена для обновления по ПК (Guild: {guild_id}, Role: {discord_role_id})")
                raise EntityNotFoundException(f"Сущность с Guild ID {guild_id}, Role ID {discord_role_id} не найдена для обновления.")

            # Преобразуем ORM-объект в DTO
            return StateEntityDiscordDTO.model_validate(updated_entity.__dict__)
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении сущности по ПК (Guild: {guild_id}, Role: {discord_role_id}): {e}", exc_info=True)
            raise

    # Изменена сигнатура: принимает StateEntityDiscordDeleteCommand (ПК в DTO)
    async def delete_entity_by_primary_key(self, command: StateEntityDiscordDeleteCommand) -> Dict[str, Any]: # Изменено
        guild_id = command.guild_id
        discord_role_id = command.discord_role_id

        try:
            # ВАЖНО: Предполагается, что delete_role_by_pk теперь принимает (guild_id, discord_role_id)
            deleted_count = await self.discord_roles_mapping_repo.delete_role_by_pk(guild_id, discord_role_id) # Изменено
            if deleted_count == 0:
                logger.info(f"Сущность не найдена для удаления по ПК (Guild: {guild_id}, Role: {discord_role_id})")
                raise EntityNotFoundException(f"Сущность с Guild ID {guild_id}, Role ID {discord_role_id} не найдена для удаления.")
            return {"message": "Сущность успешно удалена", "deleted_count": deleted_count} # Пока возвращаем dict
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении сущности по ПК (Guild: {guild_id}, Role: {discord_role_id}): {e}", exc_info=True)
            raise

    # Метод create_roles_discord принимает StateEntitiesDiscordBatchCreateCommand
    async def create_roles_discord(self, command: StateEntitiesDiscordBatchCreateCommand) -> Dict[str, Any]:
        """
        Создает или обновляет Discord роли в базе данных.
        Принимает Pydantic DTO-модель (список DTO) и возвращает словарь.
        """
        roles_batch = command.roles_batch

        # Поскольку репозиторий ожидает List[Dict], преобразуем DTO в словари
        # Каждый DTO в roles_batch содержит guild_id, discord_role_id, access_code, description
        formatted_roles_for_repo = [role_dto.model_dump(exclude_unset=True) for role_dto in roles_batch]

        if not formatted_roles_for_repo:
            logger.warning("Нет корректно отформатированных данных о ролях для сохранения (create_roles_discord).")
            raise ValueError("Нет корректно отформатированных данных о ролях для сохранения.")

        try:
            # ВАЖНО: Предполагается, что self.discord_roles_mapping_repo.create_or_update_roles_batch
            # теперь принимает List[Dict], где каждый Dict содержит все поля (включая ПК).
            return await self.discord_roles_mapping_repo.create_or_update_roles_batch(formatted_roles_for_repo)
        except Exception as e:
            logger.error(f"❌ Ошибка при массовом добавлении/обновлении ролей: {e}", exc_info=True)
            raise

    # НОВЫЙ МЕТОД: Для массового удаления по guild_id и списку discord_role_ids
    async def delete_roles_batch_by_role_ids(self, guild_id: int, discord_role_ids: List[int]) -> Dict[str, Any]:
        """
        Массово удаляет записи StateEntityDiscord по guild_id и списку discord_role_ids.
        Этот метод нужен, так как access_code не является частью ПК для удаления по списку.
        """
        logger.info(f"Начало массового удаления Discord ролей по ID для гильдии {guild_id}. Роли: {discord_role_ids}")
        try:
            # ВАЖНО: Предполагается, что в DiscordRolesMappingRepositoryImpl есть метод
            # для массового удаления, который принимает guild_id и List[discord_role_ids].
            # Если такого метода нет, нужно будет реализовать его или выполнять удаление в цикле.
            # Если репозиторий delete_roles_by_discord_ids удаляет по guild_id и List[role_id]
            deleted_count = await self.discord_roles_mapping_repo.delete_roles_by_discord_ids(
                guild_id=guild_id, # Предполагается, что метод принимает guild_id
                discord_role_ids=discord_role_ids
            )
            logger.info(f"Массовое удаление завершено. Удалено {deleted_count} ролей для гильдии {guild_id}.")
            return {"deleted_count": deleted_count}
        except Exception as e:
            logger.error(f"❌ Ошибка при массовом удалении ролей по ID для гильдии {guild_id}: {e}", exc_info=True)
            raise