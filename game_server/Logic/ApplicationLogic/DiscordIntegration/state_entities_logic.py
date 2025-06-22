# game_server/Logic/ApplicationLogic/DiscordIntegration/state_entities_logic.py

import logging
from typing import List, Dict, Any, Optional

# Импорт RepositoryManager для доступа к репозиториям PostgreSQL
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # Обновлен путь

# Импорт get_initialized_app_cache_managers для доступа к кэш-менеджерам (если потребуются)


# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# Импортируем DTO-модели из common_contracts
from game_server.common_contracts.discord_integration.discord_commands_and_events import ( # Изменено
    StateEntityDTO,
    StateEntityGetByAccessCodeCommand,
    StateEntityUpdateCommand
)

# ORM-модель StateEntity больше не импортируется напрямую в этот слой
# from game_server.database.models.models import StateEntity


class StateEntitiesLogic:
    """
    Прикладная бизнес-логика для работы с сущностями состояний (state_entities).
    Предоставляет методы для получения данных из репозитория.
    Теперь оперирует Pydantic DTO-моделями.
    """
    def __init__(self, repository_manager: RepositoryManager, cache_managers: Dict[str, Any]): # Изменено: принимаем менеджеры
        self.repository_manager = repository_manager
        # Используем репозиторий для StateEntity из RepositoryManager
        self.state_entity_repo = repository_manager.state_entities # Использование RepositoryManager.
        self.cache_managers = cache_managers # Сохраняем доступ ко всем менеджерам кэша

        logger.debug("✅ StateEntitiesLogic инициализирован.")

    # Изменена сигнатура: возвращает List[StateEntityDTO]
    async def get_all_state_entities(self) -> List[StateEntityDTO]: # Изменено
        """
        Получает список всех сущностей состояний (ролей, флагов) из базы данных.
        Возвращает список Pydantic DTO-моделей.
        """
        logger.info("Запрос на получение всех State Entities из БД.")
        try:
            # Получаем ORM-объекты из репозитория
            entities = await self.state_entity_repo.get_all_state_entities() # Изменено: используем get_all_state_entities
            
            # Преобразуем ORM-объекты в DTO-модели
            serialized_entities = [
                StateEntityDTO.model_validate(entity.__dict__) # Изменено
                for entity in entities
            ]

            logger.info(f"Найдено {len(serialized_entities)} State Entities.")
            return serialized_entities
        except Exception as e:
            logger.error(f"❌ Ошибка при получении всех State Entities: {e}", exc_info=True)
            raise

    # Изменена сигнатура: принимает StateEntityGetByAccessCodeCommand и возвращает Optional[StateEntityDTO]
    async def get_state_by_access_code(self, command: StateEntityGetByAccessCodeCommand) -> Optional[StateEntityDTO]: # Изменено
        """
        Получает сущность состояния по access_code из базы данных.
        Принимает Pydantic DTO-модель и возвращает Pydantic DTO-модель или None.
        """
        access_code = command.access_code

        logger.info(f"Запрос на получение State Entity по access_code: {access_code}.")
        try:
            entity = await self.state_entity_repo.get_state_entity_by_key(access_code) # Изменено: используем get_state_entity_by_key
            if entity:
                # Преобразуем ORM-объект в DTO-модель
                return StateEntityDTO.model_validate(entity.__dict__) # Изменено
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении State Entity по access_code '{access_code}': {e}", exc_info=True)
            raise

    # Добавляем метод update_state_entity, если он нужен в этом слое
    async def update_state_entity(self, command: StateEntityUpdateCommand) -> Optional[StateEntityDTO]:
        """
        Обновляет сущность состояния.
        Принимает Pydantic DTO-модель и возвращает Pydantic DTO-модель или None.
        """
        logger.info(f"Запрос на обновление State Entity. ID: {command.entity_id}, Key: {command.key}.")
        try:
            if command.entity_id:
                updated_entity = await self.state_entity_repo.update_state_entity(command.entity_id, command.updates)
            elif command.key:
                # Предполагается метод update_state_entity_by_key в репозитории
                # Если такого метода нет, нужно будет получить сущность по ключу, а затем обновить по ID
                existing_entity = await self.state_entity_repo.get_state_entity_by_key(command.key)
                if not existing_entity:
                    logger.warning(f"State Entity с ключом '{command.key}' не найдена для обновления.")
                    return None
                updated_entity = await self.state_entity_repo.update_state_entity(existing_entity.id, command.updates)
            else:
                raise ValueError("Необходимо предоставить entity_id или key для обновления State Entity.")

            if updated_entity:
                return StateEntityDTO.model_validate(updated_entity.__dict__)
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении State Entity: {e}", exc_info=True)
            raise