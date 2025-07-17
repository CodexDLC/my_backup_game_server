# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/core_world/game_location_repository_impl.py

import logging
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.database.models.models import GameLocation

from game_server.config.logging.logging_setup import app_logger as logger


class GameLocationRepositoryImpl(IGameLocationRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью GameLocation.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> GameLocation:
        """Создает новую запись локации мира в рамках переданной сессии."""
        new_location = GameLocation(**data)
        self._session.add(new_location)
        await self._session.flush() # flush, но НЕ commit
        # 🔥 ИЗМЕНЕНИЕ: Обновлены названия полей для логирования
        logger.info(f"Локация '{data.get('name', 'N/A')}' (type: {data.get('specific_category', 'N/A')}, skeleton: {data.get('skeleton_template_id', 'N/A')}) добавлена в сессию.")
        return new_location

    async def get_by_id(self, location_id: uuid.UUID) -> Optional[GameLocation]:
        """Получает локацию по её UUID ID в рамках переданной сессии."""
        stmt = select(GameLocation).where(GameLocation.id == location_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_access_key(self, access_key: str) -> Optional[GameLocation]:
        """Получает локацию по её access_key в рамках переданной сессии."""
        stmt = select(GameLocation).where(GameLocation.access_key == access_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[GameLocation]:
        """Получает все локации из базы данных в рамках переданной сессии."""
        # 🔥 ИЗМЕНЕНИЕ: select(GameLocation) должен автоматически выбирать новые колонки
        # Если здесь была явная выборка колонок, её нужно обновить
        stmt = select(GameLocation)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_locations_by_skeleton_template(self, skeleton_template_id: str) -> List[GameLocation]:
        """Получает все локации, принадлежащие определенному шаблону скелета мира, в рамках переданной сессии."""
        stmt = select(GameLocation).where(GameLocation.skeleton_template_id == skeleton_template_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_children_locations(self, parent_access_key: str) -> List[GameLocation]:
        """Получает все дочерние локации для заданного родительского access_key в рамках переданной сессии."""
        # 🔥 ИЗМЕНЕНИЕ: Используем GameLocation.parent_id
        stmt = select(GameLocation).where(GameLocation.parent_id == parent_access_key)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, access_key: str, updates: Dict[str, Any]) -> Optional[GameLocation]:
        """Обновляет данные локации по её access_key в рамках переданной сессии."""
        stmt = update(GameLocation).where(GameLocation.access_key == access_key).values(**updates).returning(GameLocation)
        result = await self._session.execute(stmt)
        updated_location = result.scalars().first()
        if updated_location:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Локация '{access_key}' обновлена в сессии.")
        else:
            logger.warning(f"Локация с access_key '{access_key}' не найдена для обновления.")
        return updated_location

    async def delete(self, access_key: str) -> bool:
        """Удаляет локацию по её access_key в рамках переданной сессии."""
        stmt = delete(GameLocation).where(GameLocation.access_key == access_key)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Локация '{access_key}' помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Локация '{access_key}' не найдена для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> GameLocation:
        """Создает или обновляет локацию, используя UPSERT по access_key в рамках переданной сессии."""
        access_key = data.get("access_key")
        if not access_key:
            raise ValueError("Access key must be provided for upsert operation.")

        insert_stmt = pg_insert(GameLocation).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[GameLocation.access_key], # Конфликт по access_key
            set_={
                "name": insert_stmt.excluded.name,
                "description": insert_stmt.excluded.description,
                "skeleton_template_id": insert_stmt.excluded.skeleton_template_id, # 🔥 ВОССТАНОВЛЕНО
                "specific_category": insert_stmt.excluded.specific_category, # 🔥 ИЗМЕНЕНИЕ
                "parent_id": insert_stmt.excluded.parent_id, # 🔥 ИЗМЕНЕНИЕ
                "unified_display_type": insert_stmt.excluded.unified_display_type, # 🔥 НОВОЕ
                "presentation": insert_stmt.excluded.presentation, # 🔥 НОВОЕ
                "entry_point_location_id": insert_stmt.excluded.entry_point_location_id, # 🔥 НОВОЕ
                "flavor_text_options": insert_stmt.excluded.flavor_text_options, # 🔥 НОВОЕ
                "tags": insert_stmt.excluded.tags, # 🔥 НОВОЕ
                # is_peaceful и visibility удалены
            }
        ).returning(GameLocation)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_location = result.scalar_one_or_none()
        if not upserted_location:
            raise RuntimeError("UPSERT локации не вернул объект.")
        logger.info(f"Локация '{access_key}' успешно добавлена/обновлена в сессии.")
        return upserted_location

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово вставляет или обновляет данные локаций в PostgreSQL в рамках переданной сессии.
        """
        if not data_list:
            logger.info("Список данных для UPSERT пуст. Пропускаем операцию.")
            return 0

        # 🔥 ИЗМЕНЕНИЕ: Обновляем список полей для UPSERT
        # Эти поля должны соответствовать атрибутам вашей ORM-модели GameLocation
        updatable_fields = [
            "name",
            "description",
            "skeleton_template_id", # 🔥 ВОССТАНОВЛЕНО
            "specific_category",    # 🔥 Изменено с "location_type"
            "parent_id",            # 🔥 Изменено с "parent_access_key"
            "unified_display_type", # 🔥 Новое поле
            "presentation",         # 🔥 Новое поле
            "entry_point_location_id", # 🔥 Новое поле
            "flavor_text_options",  # 🔥 Новое поле
            "tags",                 # 🔥 Новое поле
            "created_at",           # Добавьте, если хотите обновлять
            "updated_at"            # Добавьте, если хотите обновлять
            # "is_peaceful" и "visibility" удалены
        ]
        set_clause = {field: getattr(pg_insert(GameLocation).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(GameLocation).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[GameLocation.access_key], # Конфликт по access_key
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} локаций в сессии.")
        return upserted_count
