# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/background_story_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from game_server.database.models.models import BackgroundStory

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IBackgroundStoryRepository

from game_server.config.logging.logging_setup import app_logger as logger


class BackgroundStoryRepositoryImpl(IBackgroundStoryRepository):
    """
    Репозиторий для управления объектами BackgroundStory в базе данных (асинхронный).
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> BackgroundStory: # Унифицированное имя
        """Создает новую запись предыстории."""
        async with await self._get_session() as session:
            new_story = BackgroundStory(**data)
            session.add(new_story)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Предыстория '{new_story.name}' (ID: {new_story.story_id}) создана.")
                return new_story
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании предыстории '{data.get('name', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Предыстория с таким именем уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании предыстории: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[BackgroundStory]: # Унифицированное имя
        """Получает предысторию по её ID."""
        async with await self._get_session() as session:
            stmt = fselect(BackgroundStory).where(BackgroundStory.story_id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[BackgroundStory]: # Унифицированное имя
        """Получает предысторию по её внутреннему названию."""
        async with await self._get_session() as session:
            stmt = fselect(BackgroundStory).where(BackgroundStory.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self) -> List[BackgroundStory]: # Унифицированное имя
        """Возвращает все предыстории."""
        async with await self._get_session() as session:
            stmt = fselect(BackgroundStory)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[BackgroundStory]: # Унифицированное имя
        """Обновляет существующую предысторию по её ID."""
        async with await self._get_session() as session:
            stmt = update(BackgroundStory).where(BackgroundStory.story_id == id).values(**updates).returning(BackgroundStory)
            result = await session.execute(stmt)
            updated_story = result.scalars().first()
            if updated_story:
                await session.flush()
                await session.commit()
                logger.info(f"Предыстория (ID: {id}) обновлена.")
            else:
                await session.rollback()
                logger.warning(f"Предыстория с ID {id} не найдена для обновления.")
            return updated_story

    async def delete(self, id: int) -> bool: # Унифицированное имя
        """Удаляет предысторию по её ID."""
        async with await self._get_session() as session:
            stmt = delete(BackgroundStory).where(BackgroundStory.story_id == id)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.flush()
                await session.commit()
                logger.info(f"Предыстория (ID: {id}) удалена.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Предыстория (ID: {id}) не найдена для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> BackgroundStory: # Унифицированное имя
        """Создает или обновляет запись BackgroundStory, используя upsert."""
        name = data.get("name")
        if not name:
            raise ValueError("Name must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
                insert_stmt = pg_insert(BackgroundStory).values(**data)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[BackgroundStory.name],
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

                result = await session.execute(on_conflict_stmt)
                await session.commit()

                new_story = result.scalar_one_or_none()
                if not new_story:
                    raise RuntimeError("UPSERT не вернул объект.")
                logger.info(f"Предыстория '{new_story.name}' (ID: {new_story.story_id}) успешно добавлена/обновлена.")
                return new_story
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT предыстории '{data.get('name', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении предыстории: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT предыстории '{data.get('name', 'N/A')}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # Добавлен
        """Массово создает или обновляет предыстории."""
        if not data_list:
            logger.info("Пустой список данных для BackgroundStory upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
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
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} предысторий.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT предысторий: {e}", exc_info=True)
                raise