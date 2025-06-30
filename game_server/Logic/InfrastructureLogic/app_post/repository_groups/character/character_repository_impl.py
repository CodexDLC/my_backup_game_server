# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/character_repository_impl.py

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, String, update # Добавлен 'update' для update_character
# from sqlalchemy.future import select as fselect # fselect не требуется, просто select
from sqlalchemy.exc import IntegrityError # Может быть полезен, хотя для CharacterRepository не так часто

# Убедитесь, что путь к вашей модели Character корректен
from game_server.database.models.models import Character, AccountInfo # AccountInfo может понадобиться для связей

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class CharacterRepositoryImpl(ICharacterRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью Character.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронно).
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_character(self, character_data: Dict[str, Any]) -> Character:
        """
        Создает нового персонажа.
        :param character_data: Словарь с данными для нового персонажа.
        :return: Созданный объект Character.
        :raises ValueError: Если имя персонажа уже занято (если оно должно быть уникальным).
        """
        try:
            new_character = Character(**character_data)
            self.db_session.add(new_character)
            await self.db_session.flush() # Используем flush, чтобы получить ID
            logger.info(f"Персонаж '{new_character.name if hasattr(new_character, 'name') else 'N/A'}' добавлен в сессию.")
            return new_character
        except Exception as e:
            await self.db_session.rollback() # Откат при ошибке
            logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
            raise

    async def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """Получение персонажа по ID."""
        query = select(Character).where(Character.character_id == character_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_character_by_name(self, name: str) -> Optional[Character]:
        """Получает персонажа по имени."""
        query = select(Character).where(Character.name == name)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_characters_by_account_id(self, account_id: int) -> List[Character]:
        """Получает всех персонажей, принадлежащих аккаунту, которые не удалены."""
        query = select(Character).where(
            (Character.account_id == account_id) & 
            (Character.is_deleted == False)
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def update_character(self, character_id: int, update_data: Dict[str, Any]) -> Optional[Character]:
        """
        Обновление данных персонажа.
        """
        stmt = update(Character).where(Character.character_id == character_id).values(**update_data).returning(Character)
        result = await self.db_session.execute(stmt)
        updated_character = result.scalars().first()
        if updated_character:
            updated_character.updated_at = datetime.now(timezone.utc) # Обновляем время изменения
            await self.db_session.flush() # Используем flush
            logger.info(f"Персонаж {character_id} обновлен в сессии.")
        else:
            logger.warning(f"Персонаж с ID {character_id} не найден для обновления.")
        return updated_character

    async def soft_delete_character(self, character_id: int) -> bool:
        """
        Логическое удаление персонажа (установка is_deleted в True).
        """
        character = await self.get_character_by_id(character_id)
        if not character:
            logger.warning(f"Персонаж с ID {character_id} не найден для логического удаления.")
            return False

        character.is_deleted = True
        character.updated_at = datetime.now(timezone.utc)
        await self.db_session.flush() # Используем flush
        logger.info(f"Персонаж {character_id} логически удален в сессии.")
        return True

    async def get_online_character_by_account_id(self, account_id: int) -> Optional[Character]:
        """
        Получает персонажа со статусом 'online' для данного аккаунта.
        Предполагается, что только один персонаж может быть 'online' одновременно.
        """
        query = select(Character).where(
            (Character.account_id == account_id) & 
            (Character.status == "online") &
            (Character.is_deleted == False)
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()