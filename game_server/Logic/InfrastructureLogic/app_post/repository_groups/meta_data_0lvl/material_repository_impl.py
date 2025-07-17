# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/material_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Material

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IMaterialRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class MaterialRepositoryImpl(IMaterialRepository):
    """
    Репозиторий для управления объектами Material в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> Material:
        """Создает новую запись материала в рамках переданной сессии."""
        new_material = Material(**data)
        self._session.add(new_material)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Материал '{new_material.material_code}' добавлен в сессию.")
        return new_material

    async def get_by_id(self, id: str) -> Optional[Material]:
        """Получает материал по его коду в рамках переданной сессии."""
        return await self.get_material_by_code(id) # Вызываем существующий специфичный метод

    async def get_material_by_code(self, material_code: str) -> Optional[Material]:
        """Получает материал по его коду в рамках переданной сессии."""
        stmt = fselect(Material).where(Material.material_code == material_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Material]:
        """Получает все материалы из базы данных в рамках переданной сессии."""
        stmt = fselect(Material)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Material]:
        """Обновляет существующий материал по его коду в рамках переданной сессии."""
        return await self.update_material(id, updates) # Вызываем существующий специфичный метод

    async def update_material(self, material_code: str, updates: Dict[str, Any]) -> Optional[Material]:
        """Обновляет существующий материал по его коду в рамках переданной сессии."""
        stmt = update(Material).where(Material.material_code == material_code).values(**updates).returning(Material)
        result = await self._session.execute(stmt)
        updated_material = result.scalars().first()
        if updated_material:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Материал '{material_code}' обновлен в сессии.")
        else:
            logger.warning(f"Материал с кодом '{material_code}' не найден для обновления.")
        return updated_material

    async def delete(self, id: str) -> bool:
        """Удаляет материал по его коду в рамках переданной сессии."""
        return await self.delete_material(id) # Вызываем существующий специфичный метод

    async def delete_material(self, material_code: str) -> bool:
        """Удаляет материал по его коду в рамках переданной сессии."""
        stmt = delete(Material).where(Material.material_code == material_code)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Материал '{material_code}' помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Материал '{material_code}' не найден для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> Material:
        """Создает или обновляет материал, используя UPSERT в рамках переданной сессии."""
        return await self.upsert_material(data) # Вызываем существующий специфичный метод

    async def upsert_material(self, data: Dict[str, Any]) -> Material:
        """Создает или обновляет материал, используя UPSERT в рамках переданной сессии."""
        material_code = data.get("material_code")
        if not material_code:
            raise ValueError("Material code must be provided for upsert operation.")

        insert_stmt = pg_insert(Material).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Material.material_code],
            set_={
                "name": insert_stmt.excluded.name,
                "type": insert_stmt.excluded.type,
                "material_category": insert_stmt.excluded.material_category,
                "rarity_level": insert_stmt.excluded.rarity_level,
                "adjective": insert_stmt.excluded.adjective,
                "color": insert_stmt.excluded.color,
                "is_fragile": insert_stmt.excluded.is_fragile,
                "strength_percentage": insert_stmt.excluded.strength_percentage,
            }
        ).returning(Material)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_material = result.scalar_one_or_none()
        if not upserted_material:
            raise RuntimeError("UPSERT материала не вернул объект.")
        logger.info(f"Материал '{material_code}' успешно добавлен/обновлен в сессии.")
        return upserted_material

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет материалы в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для Material upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "name", "type", "material_category", "rarity_level",
            "adjective", "color", "is_fragile", "strength_percentage",
        ]
        set_clause = {field: getattr(pg_insert(Material).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(Material).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Material.material_code],
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} материалов в сессии.")
        return upserted_count
