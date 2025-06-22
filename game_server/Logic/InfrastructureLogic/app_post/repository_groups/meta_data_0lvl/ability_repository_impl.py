# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/ability_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload # Убедимся, что import есть

from game_server.database.models.models import Ability # Убедитесь, что модель Ability корректна

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IAbilityRepository

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class AbilityRepositoryImpl(IAbilityRepository):
    """
    Репозиторий для управления объектами Ability в базе данных (асинхронный).
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> Ability:
        """Создает новую запись способности."""
        async with await self._get_session() as session:
            new_ability = Ability(**data)
            session.add(new_ability)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Способность '{new_ability.name}' (key: {new_ability.ability_key}) создана.")
                return new_ability
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании способности '{data.get('ability_key', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Способность с таким ключом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании способности: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[Ability]:
        """Получает способность по её ID (ability_id)."""
        async with await self._get_session() as session:
            stmt = fselect(Ability).where(Ability.ability_id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_key(self, key: str) -> Optional[Ability]:
        """Получает способность по её уникальному ключу (ability_key)."""
        async with await self._get_session() as session:
            stmt = fselect(Ability).where(Ability.ability_key == key)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self) -> List[Ability]:
        """Получает все способности из базы данных."""
        async with await self._get_session() as session:
            stmt = fselect(Ability)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Ability]:
        """Обновляет существующую способность по её ID (ability_id)."""
        async with await self._get_session() as session:
            stmt = update(Ability).where(Ability.ability_id == id).values(**updates).returning(Ability)
            result = await session.execute(stmt)
            updated_ability = result.scalars().first()
            if updated_ability:
                await session.flush()
                await session.commit()
                logger.info(f"Способность (ID: {id}) обновлена.")
            else:
                await session.rollback()
                logger.warning(f"Способность с ID {id} не найдена для обновления.")
            return updated_ability

    async def delete(self, id: int) -> bool:
        """Удаляет способность по её ID (ability_id)."""
        async with await self._get_session() as session:
            stmt = delete(Ability).where(Ability.ability_id == id)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.flush()
                await session.commit()
                logger.info(f"Способность (ID: {id}) удалена.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Способность с ID {id} не найдена для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> Ability:
        """Создает или обновляет способность, используя UPSERT (конфликт по ability_key)."""
        ability_key = data.get("ability_key")
        if not ability_key:
            raise ValueError("Ability key must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
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

                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_ability = result.scalar_one_or_none()
                if not upserted_ability:
                    raise RuntimeError("UPSERT способности не вернул объект.")
                logger.info(f"Способность '{ability_key}' успешно добавлена/обновлена.")
                return upserted_ability
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT способности '{ability_key}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении способности: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT способности '{ability_key}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет способности."""
        if not data_list:
            logger.info("Пустой список данных для Ability upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
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
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} способностей.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT способностей: {e}", exc_info=True)
                raise

    async def get_ability_with_skill_requirement(self, ability_key: str) -> Optional[Ability]:
        """Получает способность по её ключу с жадной загрузкой связанного навыка."""
        async with await self._get_session() as session:
            stmt = fselect(Ability).where(Ability.ability_key == ability_key).options(
                selectinload(Ability.skill_requirement)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()