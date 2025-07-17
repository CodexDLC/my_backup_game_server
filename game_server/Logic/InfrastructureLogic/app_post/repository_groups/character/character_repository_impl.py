# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/character_repository_impl.py

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from game_server.database.models.models import Character, CharacterSkills

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository

from game_server.config.logging.logging_setup import app_logger as logger


class CharacterRepositoryImpl(ICharacterRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью Character.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_character(self, character_data: Dict[str, Any]) -> Character:
        """
        Создает нового персонажа в рамках переданной сессии.
        :param character_data: Словарь с данными для нового персонажа.
        :return: Созданный объект Character.
        """
        new_character = Character(**character_data)
        self._session.add(new_character)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Персонаж '{new_character.name if hasattr(new_character, 'name') else 'N/A'}' добавлен в сессию.")
        return new_character

    async def get_full_character_data_by_id(self, character_id: int) -> Optional[Character]:
        """
        Получает персонажа со всеми связанными данными (для формирования кэша) в рамках переданной сессии.
        Использует 'жадную' загрузку (eager loading).
        """
        stmt = (
            select(Character)
            .where(Character.character_id == character_id)
            .options(
                selectinload(Character.special_stats),
                selectinload(Character.character_skills).selectinload(CharacterSkills.skills),
                selectinload(Character.personality),
                selectinload(Character.background_story),
                selectinload(Character.clan)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """Получение персонажа по ID в рамках переданной сессии."""
        query = select(Character).where(Character.character_id == character_id)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def get_character_by_name(self, name: str) -> Optional[Character]:
        """Получает персонажа по имени в рамках переданной сессии."""
        query = select(Character).where(Character.name == name)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def get_characters_by_account_id(self, account_id: int) -> List[Character]:
        """Получает всех персонажей, принадлежащих аккаунту, которые не удалены, в рамках переданной сессии."""
        query = select(Character).where(
            (Character.account_id == account_id) &
            (Character.is_deleted == False)
        )
        result = await self._session.execute(query)
        return result.scalars().all()

    async def update_character(self, character_id: int, update_data: Dict[str, Any]) -> Optional[Character]:
        """
        Обновление данных персонажа в рамках переданной сессии.
        """
        stmt = update(Character).where(Character.character_id == character_id).values(**update_data).returning(Character)
        result = await self._session.execute(stmt)
        updated_character = result.scalars().first()
        if updated_character:
            updated_character.updated_at = datetime.now(timezone.utc)
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Персонаж {character_id} обновлен в сессии.")
        else:
            logger.warning(f"Персонаж с ID {character_id} не найден для обновления.")
        return updated_character

    async def soft_delete_character(self, character_id: int) -> bool:
        """
        Логическое удаление персонажа (установка is_deleted в True) в рамках переданной сессии.
        """
        query = select(Character).where(Character.character_id == character_id)
        result = await self._session.execute(query)
        character_to_delete = result.scalars().first()

        if not character_to_delete:
            logger.warning(f"Персонаж с ID {character_id} не найден для логического удаления.")
            return False

        character_to_delete.is_deleted = True
        character_to_delete.updated_at = datetime.now(timezone.utc)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Персонаж {character_id} логически удален в сессии.")
        return True

    async def get_online_character_by_account_id(self, account_id: int) -> Optional[Character]:
        """
        Получает персонажа со статусом 'online' для данного аккаунта в рамках переданной сессии.
        Предполагается, что только один персонаж может быть 'online' одновременно.
        """
        query = select(Character).where(
            (Character.account_id == account_id) &
            (Character.status == "online") &
            (Character.is_deleted == False)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
