# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/material_repository_impl.py

import logging
from typing import List, Dict, Any, Optional, Type # ДОБАВЛЕНО Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound # ДОБАВЛЕНО NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Material

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IMaterialRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class MaterialRepositoryImpl(IMaterialRepository):
    """
    Репозиторий для управления объектами Material в базе данных (асинхронный).
    """
    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> Material: # ИЗМЕНЕНО: Унифицированное имя
        """Создает новую запись материала в базе данных."""
        async with await self._get_session() as session:
            new_material = Material(**data)
            session.add(new_material)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Материал '{new_material.material_code}' создан.")
                return new_material
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании материала '{data.get('material_code', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Материал с таким кодом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании материала '{data.get('material_code', 'N/A')}': {e}", exc_info=True)
                raise

    async def get_by_id(self, id: str) -> Optional[Material]: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Получает материал по его коду."""
        return await self.get_material_by_code(id) # Вызываем существующий специфичный метод

    async def get_material_by_code(self, material_code: str) -> Optional[Material]: # Оригинальное имя
        """Получает материал по его коду."""
        async with await self._get_session() as session:
            stmt = fselect(Material).where(Material.material_code == material_code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self) -> List[Material]:
        """Получает все материалы из базы данных."""
        async with await self._get_session() as session:
            stmt = fselect(Material)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Material]: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Обновляет существующий материал по его коду."""
        return await self.update_material(id, updates) # Вызываем существующий специфичный метод

    async def update_material(self, material_code: str, updates: Dict[str, Any]) -> Optional[Material]: # Оригинальное имя
        """Обновляет существующий материал по его коду."""
        async with await self._get_session() as session:
            stmt = update(Material).where(Material.material_code == material_code).values(**updates).returning(Material)
            result = await session.execute(stmt)
            updated_material = result.scalars().first()
            if updated_material:
                await session.flush()
                await session.commit()
                logger.info(f"Материал '{material_code}' обновлен.")
            else:
                await session.rollback()
                logger.warning(f"Материал с кодом '{material_code}' не найден для обновления.")
            return updated_material

    async def delete(self, id: str) -> bool: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Удаляет материал по его коду."""
        return await self.delete_material(id) # Вызываем существующий специфичный метод

    async def delete_material(self, material_code: str) -> bool: # Оригинальное имя
        """Удаляет материал по его коду."""
        async with await self._get_session() as session:
            stmt = delete(Material).where(Material.material_code == material_code)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.flush()
                await session.commit()
                logger.info(f"Материал '{material_code}' удален.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Материал '{material_code}' не найден для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> Material: # ИЗМЕНЕНО: Унифицированное имя
        """Создает или обновляет материал, используя UPSERT."""
        return await self.upsert_material(data) # Вызываем существующий специфичный метод

    async def upsert_material(self, data: Dict[str, Any]) -> Material: # Оригинальное имя
        """Создает или обновляет материал, используя UPSERT."""
        material_code = data.get("material_code")
        if not material_code:
            raise ValueError("Material code must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
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

                result = await session.execute(on_conflict_stmt)
                await session.flush()
                await session.commit()

                upserted_material = result.scalar_one_or_none()
                if not upserted_material:
                    raise RuntimeError("UPSERT материала не вернул объект.")
                logger.info(f"Материал '{material_code}' успешно добавлен/обновлен.")
                return upserted_material
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT материала '{material_code}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении материала: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT материала '{material_code}': {e}", exc_info=True)
                raise
    
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # ДОБАВЛЕНО: Унифицированное имя
        """Массово создает или обновляет материалы."""
        if not data_list:
            logger.info("Пустой список данных для Material upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
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
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} материалов.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT материалов: {e}", exc_info=True)
                raise