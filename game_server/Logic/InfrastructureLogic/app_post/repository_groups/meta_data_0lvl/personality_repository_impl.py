# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/personality_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Personality

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IPersonalityRepository

from game_server.config.logging.logging_setup import app_logger as logger


class PersonalityRepositoryImpl(IPersonalityRepository):
    """
    Репозиторий для управления объектами Personality в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> Personality:
        """Создает новую запись личности в рамках переданной сессии."""
        new_personality = Personality(**data)
        self._session.add(new_personality)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Личность '{new_personality.name}' (ID: {new_personality.personality_id}) добавлена в сессию.")
        return new_personality

    async def get_by_id(self, id: int) -> Optional[Personality]:
        """Получает личность по её ID в рамках переданной сессии."""
        stmt = fselect(Personality).where(Personality.personality_id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Personality]:
        """Получает личность по её названию в рамках переданной сессии."""
        stmt = fselect(Personality).where(Personality.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Personality]:
        """Возвращает все личности из базы данных в рамках переданной сессии."""
        stmt = fselect(Personality)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Personality]:
        """Обновляет существующую личность по её ID в рамках переданной сессии."""
        stmt = update(Personality).where(Personality.personality_id == id).values(**updates).returning(Personality)
        result = await self._session.execute(stmt)
        updated_personality = result.scalars().first()
        if updated_personality:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Личность (ID: {id}) обновлена в сессии.")
        else:
            logger.warning(f"Личность с ID {id} не найдена для обновления.")
        return updated_personality

    async def delete(self, id: int) -> bool:
        """Удаляет личность по её ID в рамках переданной сессии."""
        stmt = delete(Personality).where(Personality.personality_id == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Личность (ID: {id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Личность с ID {id} не найдена для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> Personality:
        """
        Создает или обновляет запись Personality, используя upsert (INSERT ON CONFLICT DO UPDATE) в рамках переданной сессии.
        Конфликт определяется по 'name' (уникальное поле).
        """
        name = data.get("name") # Используем name, так как оно является уникальным
        if not name:
            raise ValueError("Name must be provided for upsert operation.")

        insert_stmt = pg_insert(Personality).values(**data)

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Personality.name], # Конфликт по уникальному имени (name)
            set_={
                "description": insert_stmt.excluded.description,
                "personality_group": insert_stmt.excluded.personality_group,
                "behavior_tags": insert_stmt.excluded.behavior_tags,
                "dialogue_modifiers": insert_stmt.excluded.dialogue_modifiers,
                "combat_ai_directives": insert_stmt.excluded.combat_ai_directives,
                "quest_interaction_preferences": insert_stmt.excluded.quest_interaction_preferences,
                "trait_associations": insert_stmt.excluded.trait_associations,
                "applicable_game_roles": insert_stmt.excluded.applicable_game_roles,
                "rarity_weight": insert_stmt.excluded.rarity_weight,
                "ai_priority_level": insert_stmt.excluded.ai_priority_level,
            }
        ).returning(Personality)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_personality = result.scalar_one_or_none()
        if not upserted_personality:
            raise RuntimeError("UPSERT личности не вернул объект.")
        logger.info(f"Личность '{upserted_personality.name}' (Key: {name}) успешно добавлена/обновлена в сессии.")
        return upserted_personality

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет личности в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для Personality upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "name", "description", "personality_group", "behavior_tags",
            "dialogue_modifiers", "combat_ai_directives", "quest_interaction_preferences",
            "trait_associations", "applicable_game_roles", "rarity_weight",
            "ai_priority_level",
        ]
        set_clause = {field: getattr(pg_insert(Personality).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(Personality).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Personality.name], # Конфликт по уникальному имени
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} личностей в сессии.")
        return upserted_count
