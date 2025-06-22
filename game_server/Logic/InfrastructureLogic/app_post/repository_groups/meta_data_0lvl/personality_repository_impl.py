# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/personality_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type # ДОБАВЛЕНО Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update # Добавлено update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, NoResultFound # ДОБАВЛЕНО NoResultFound

from game_server.database.models.models import Personality

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IPersonalityRepository

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class PersonalityRepositoryImpl(IPersonalityRepository):
    """
    Репозиторий для управления объектами Personality в базе данных (асинхронный).
    """
    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> Personality: # ИЗМЕНЕНО: Унифицированное имя
        """Создает новую запись личности."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            new_personality = Personality(**data)
            session.add(new_personality)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Личность '{new_personality.name}' (ID: {new_personality.personality_id}) создана.")
                return new_personality
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании личности '{data.get('name', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Личность с таким именем уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании личности: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[Personality]: # ИЗМЕНЕНО: Унифицированное имя
        """Получает личность по её ID."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(Personality).where(Personality.personality_id == id)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Personality]: # ИЗМЕНЕНО: Унифицированное имя
        """Получает личность по её названию."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(Personality).where(Personality.name == name)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_all(self) -> List[Personality]: # ИЗМЕНЕНО: Унифицированное имя
        """Возвращает все личности."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(Personality)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Personality]: # ИЗМЕНЕНО: Унифицированное имя
        """Обновляет существующую личность по её ID."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = update(Personality).where(Personality.personality_id == id).values(**updates).returning(Personality)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            updated_personality = result.scalars().first()
            if updated_personality:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Личность (ID: {id}) обновлена.")
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Личность с ID {id} не найдена для обновления.")
            return updated_personality

    async def delete(self, id: int) -> bool: # ИЗМЕНЕНО: Унифицированное имя
        """Удаляет личность по её ID."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = delete(Personality).where(Personality.personality_id == id)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            if result.rowcount > 0:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Личность (ID: {id}) удалена.")
                return True
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Личность с ID {id} не найдена для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> Personality: # ИЗМЕНЕНО: Унифицированное имя
        """
        Создает или обновляет запись Personality, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Конфликт определяется по 'name' (уникальное поле).
        """
        name = data.get("name") # Используем name, так как оно является уникальным
        if not name:
            raise ValueError("Name must be provided for upsert operation.")

        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
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

                result = await session.execute(on_conflict_stmt) # ИЗМЕНЕНО
                await session.commit() # ДОБАВЛЕНО commit

                upserted_personality = result.scalar_one_or_none()
                if not upserted_personality:
                    raise RuntimeError("UPSERT личности не вернул объект.")
                logger.info(f"Личность '{upserted_personality.name}' (Key: {name}) успешно добавлена/обновлена.")
                return upserted_personality
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT личности '{name}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении личности: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT личности '{name}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # ДОБАВЛЕНО: Унифицированное имя
        """Массово создает или обновляет личности."""
        if not data_list:
            logger.info("Пустой список данных для Personality upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
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
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} личностей.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT личностей: {e}", exc_info=True)
                raise