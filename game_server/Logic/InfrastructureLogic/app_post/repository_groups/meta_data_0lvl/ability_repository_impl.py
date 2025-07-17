# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/ability_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from game_server.database.models.models import Ability

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IAbilityRepository

from game_server.config.logging.logging_setup import app_logger as logger


class AbilityRepositoryImpl(IAbilityRepository):
    """
    Репозиторий для управления объектами Ability в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> Ability:
        """Создает новую запись способности в рамках переданной сессии."""
        new_ability = Ability(**data)
        self._session.add(new_ability)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Способность '{new_ability.name}' (key: {new_ability.ability_key}) добавлена в сессию.")
        return new_ability

    async def get_by_id(self, id: int) -> Optional[Ability]:
        """Получает способность по её ID (ability_id) в рамках переданной сессии."""
        stmt = fselect(Ability).where(Ability.ability_id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str) -> Optional[Ability]:
        """Получает способность по её уникальному ключу (ability_key) в рамках переданной сессии."""
        stmt = fselect(Ability).where(Ability.ability_key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Ability]:
        """Получает все способности из базы данных в рамках переданной сессии."""
        stmt = fselect(Ability)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Ability]:
        """Обновляет существующую способность по её ID (ability_id) в рамках переданной сессии."""
        stmt = update(Ability).where(Ability.ability_id == id).values(**updates).returning(Ability)
        result = await self._session.execute(stmt)
        updated_ability = result.scalars().first()
        if updated_ability:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Способность (ID: {id}) обновлена в сессии.")
        else:
            logger.warning(f"Способность с ID {id} не найдена для обновления.")
        return updated_ability

    async def delete(self, id: int) -> bool:
        """Удаляет способность по её ID (ability_id) в рамках переданной сессии."""
        stmt = delete(Ability).where(Ability.ability_id == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Способность (ID: {id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Способность с ID {id} не найдена для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> Ability:
        """Создает или обновляет способность, используя UPSERT (конфликт по ability_key) в рамках переданной сессии."""
        ability_key = data.get("ability_key")
        if not ability_key:
            raise ValueError("Ability key must be provided for upsert operation.")

        insert_stmt = pg_insert(Ability).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Ability.ability_key],
            set_={
                "name": insert_stmt.excluded.name,
                "description": insert_stmt.excluded.description,
                "ability_type": insert_stmt.excluded.ability_type,
                "required_skill_key": insert_stmt.excluded.required_skill_key,
                "required_skill_level": insert_stmt.excluded.required_skill_level,
                "required_stats": insert_stmt.excluded.required_stats,
                "required_items": insert_stmt.excluded.required_items,
                "cost_type": insert_stmt.excluded.cost_type,
                "cost_amount": insert_stmt.excluded.cost_amount,
                "cooldown_seconds": insert_stmt.excluded.cooldown_seconds,
                "cast_time_ms": insert_stmt.excluded.cast_time_ms,
                "effect_data": insert_stmt.excluded.effect_data,
                "animation_key": insert_stmt.excluded.animation_key,
                "sfx_key": insert_stmt.excluded.sfx_key,
                "vfx_key": insert_stmt.excluded.vfx_key,
            }
        ).returning(Ability)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_ability = result.scalar_one_or_none()
        if not upserted_ability:
            raise RuntimeError("UPSERT способности не вернул объект.")
        logger.info(f"Способность '{ability_key}' успешно добавлена/обновлена в сессии.")
        return upserted_ability

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет способности в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для Ability upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "name", "description", "ability_type", "required_skill_key",
            "required_skill_level", "required_stats", "required_items",
            "cost_type", "cost_amount", "cooldown_seconds", "cast_time_ms",
            "effect_data", "animation_key", "sfx_key", "vfx_key",
        ]
        set_clause = {field: getattr(pg_insert(Ability).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(Ability).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Ability.ability_key],
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} способностей в сессии.")
        return upserted_count

    async def get_ability_with_skill_requirement(self, ability_key: str) -> Optional[Ability]:
        """Получает способность по её ключу с жадной загрузкой связанного навыка в рамках переданной сессии."""
        stmt = fselect(Ability).where(Ability.ability_key == ability_key).options(
            selectinload(Ability.skill_requirement)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
