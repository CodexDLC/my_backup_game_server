# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/core_world/game_location_repository_impl.py

import logging
import uuid
from typing import Optional, Dict, Any, List, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert # Для upsert_many и upsert

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.database.models.models import GameLocation

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class GameLocationRepositoryImpl(IGameLocationRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью GameLocation.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронно).
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> GameLocation:
        """Создает новую запись локации мира."""
        async with await self._get_session() as session:
            new_location = GameLocation(**data)
            session.add(new_location)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Локация '{data.get('name', 'N/A')}' (type: {data.get('location_type', 'N/A')}, skeleton: {data.get('skeleton_template_id', 'N/A')}) создана.")
                return new_location
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании локации '{data.get('name', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Локация с таким access_key или ID уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании локации '{data.get('name', 'N/A')}': {e}", exc_info=True)
                raise

    async def get_by_id(self, location_id: uuid.UUID) -> Optional[GameLocation]:
        """Получает локацию по её UUID ID."""
        async with await self._get_session() as session:
            stmt = select(GameLocation).where(GameLocation.id == location_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_access_key(self, access_key: str) -> Optional[GameLocation]:
        """Получает локацию по её access_key."""
        async with await self._get_session() as session:
            stmt = select(GameLocation).where(GameLocation.access_key == access_key)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self) -> List[GameLocation]:
        """Получает все локации из базы данных."""
        async with await self._get_session() as session:
            stmt = select(GameLocation)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_locations_by_skeleton_template(self, skeleton_template_id: str) -> List[GameLocation]:
        """Получает все локации, принадлежащие определенному шаблону скелета мира."""
        async with await self._get_session() as session:
            stmt = select(GameLocation).where(GameLocation.skeleton_template_id == skeleton_template_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_children_locations(self, parent_access_key: str) -> List[GameLocation]:
        """Получает все дочерние локации для заданного родительского access_key."""
        async with await self._get_session() as session:
            stmt = select(GameLocation).where(GameLocation.parent_access_key == parent_access_key)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, access_key: str, updates: Dict[str, Any]) -> Optional[GameLocation]:
        """Обновляет данные локации по её access_key."""
        async with await self._get_session() as session:
            stmt = update(GameLocation).where(GameLocation.access_key == access_key).values(**updates).returning(GameLocation)
            result = await session.execute(stmt)
            updated_location = result.scalars().first()
            if updated_location:
                await session.flush()
                await session.commit()
                logger.info(f"Локация '{access_key}' обновлена.")
            else:
                await session.rollback()
                logger.warning(f"Локация с access_key '{access_key}' не найдена для обновления.")
            return updated_location

    async def delete(self, access_key: str) -> bool:
        """Удаляет локацию по её access_key."""
        async with await self._get_session() as session:
            stmt = delete(GameLocation).where(GameLocation.access_key == access_key)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.flush()
                await session.commit()
                logger.info(f"Локация '{access_key}' удалена.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Локация '{access_key}' не найдена для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> GameLocation:
        """Создает или обновляет локацию, используя UPSERT по access_key."""
        access_key = data.get("access_key")
        if not access_key:
            raise ValueError("Access key must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
                insert_stmt = pg_insert(GameLocation).values(**data)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[GameLocation.access_key], # Конфликт по access_key
                    set_={
                        "name": insert_stmt.excluded.name,
                        "description": insert_stmt.excluded.description,
                        "location_type": insert_stmt.excluded.location_type,
                        "parent_access_key": insert_stmt.excluded.parent_access_key,
                        "skeleton_template_id": insert_stmt.excluded.skeleton_template_id,
                        # Добавьте сюда все поля, которые вы хотите обновлять при конфликте
                    }
                ).returning(GameLocation)

                result = await session.execute(on_conflict_stmt)
                await session.flush()
                await session.commit()

                upserted_location = result.scalar_one_or_none()
                if not upserted_location:
                    raise RuntimeError("UPSERT локации не вернул объект.")
                logger.info(f"Локация '{access_key}' успешно добавлена/обновлена.")
                return upserted_location
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT локации '{access_key}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении локации: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT локации '{access_key}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет локации."""
        if not data_list:
            logger.info("Пустой список данных для GameLocation upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
                # Определяем обновляемые поля.
                # Важно: здесь должны быть ВСЕ поля, которые могут быть обновлены, кроме PK
                updatable_fields = [
                    "name", "description", "location_type", "parent_access_key", "skeleton_template_id"
                    # Добавьте сюда остальные поля модели GameLocation, которые могут обновляться
                ]
                set_clause = {field: getattr(pg_insert(GameLocation).excluded, field) for field in updatable_fields}

                insert_stmt = pg_insert(GameLocation).values(data_list)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[GameLocation.access_key], # Конфликт по access_key
                    set_=set_clause
                )
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} локаций.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT локаций: {e}", exc_info=True)
                raise