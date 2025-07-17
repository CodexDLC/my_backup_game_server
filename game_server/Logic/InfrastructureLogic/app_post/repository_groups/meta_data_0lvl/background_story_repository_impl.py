# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/background_story_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import BackgroundStory

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IBackgroundStoryRepository

from game_server.config.logging.logging_setup import app_logger as logger


class BackgroundStoryRepositoryImpl(IBackgroundStoryRepository):
    """
    Репозиторий для управления объектами BackgroundStory в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> BackgroundStory:
        """Создает новую запись предыстории в рамках переданной сессии."""
        new_story = BackgroundStory(**data)
        self._session.add(new_story)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Предыстория '{new_story.name}' (ID: {new_story.story_id}) добавлена в сессию.")
        return new_story

    async def get_by_id(self, id: int) -> Optional[BackgroundStory]:
        """Получает предысторию по её ID в рамках переданной сессии."""
        stmt = fselect(BackgroundStory).where(BackgroundStory.story_id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[BackgroundStory]:
        """Получает предысторию по её внутреннему названию в рамках переданной сессии."""
        stmt = fselect(BackgroundStory).where(BackgroundStory.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[BackgroundStory]:
        """Возвращает все предыстории из базы данных в рамках переданной сессии."""
        stmt = fselect(BackgroundStory)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[BackgroundStory]:
        """Обновляет существующую предысторию по её ID в рамках переданной сессии."""
        stmt = update(BackgroundStory).where(BackgroundStory.story_id == id).values(**updates).returning(BackgroundStory)
        result = await self._session.execute(stmt)
        updated_story = result.scalars().first()
        if updated_story:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Предыстория (ID: {id}) обновлена в сессии.")
        else:
            logger.warning(f"Предыстория с ID {id} не найдена для обновления.")
        return updated_story

    async def delete(self, id: int) -> bool:
        """Удаляет предысторию по её ID в рамках переданной сессии."""
        stmt = delete(BackgroundStory).where(BackgroundStory.story_id == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Предыстория (ID: {id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Предыстория (ID: {id}) не найдена для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> BackgroundStory:
        """Создает или обновляет запись BackgroundStory, используя upsert (INSERT ON CONFLICT DO UPDATE) в рамках переданной сессии."""
        name = data.get("name")
        if not name:
            raise ValueError("Name must be provided for upsert operation.")

        insert_stmt = pg_insert(BackgroundStory).values(**data)

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[BackgroundStory.name], # Конфликт по уникальному имени (name)
            set_={
                "display_name": insert_stmt.excluded.display_name,
                "short_description": insert_stmt.excluded.short_description,
                "stat_modifiers": insert_stmt.excluded.stat_modifiers,
                "skill_affinities": insert_stmt.excluded.skill_affinities,
                "initial_inventory_items": insert_stmt.excluded.initial_inventory_items,
                "starting_location_tags": insert_stmt.excluded.starting_location_tags,
                "lore_fragments": insert_stmt.excluded.lore_fragments,
                "potential_factions": insert_stmt.excluded.potential_factions,
                "rarity_weight": insert_stmt.excluded.rarity_weight,
            }
        ).returning(BackgroundStory)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_story = result.scalar_one_or_none()
        if not upserted_story:
            raise RuntimeError("UPSERT предыстории не вернул объект.")
        logger.info(f"Предыстория '{upserted_story.name}' (Key: {name}) успешно добавлена/обновлена в сессии.")
        return upserted_story

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет предыстории в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для BackgroundStory upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "display_name", "short_description", "stat_modifiers",
            "skill_affinities", "initial_inventory_items", "starting_location_tags",
            "lore_fragments", "potential_factions", "rarity_weight",
        ]
        set_clause = {field: getattr(pg_insert(BackgroundStory).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(BackgroundStory).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[BackgroundStory.name], # Конфликт по уникальному имени
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} предысторий в сессии.")
        return upserted_count
