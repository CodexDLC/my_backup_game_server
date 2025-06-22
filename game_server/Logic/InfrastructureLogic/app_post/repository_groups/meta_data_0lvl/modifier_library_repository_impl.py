# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/modifier_library_repository_impl.py

import logging
from typing import List, Dict, Any, Optional, Type # ДОБАВЛЕНО Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound # ДОБАВЛЕНО NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import ModifierLibrary

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IModifierLibraryRepository

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class ModifierLibraryRepositoryImpl(IModifierLibraryRepository):
    """
    Репозиторий для управления объектами ModifierLibrary в базе данных (асинхронный).
    """
    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> ModifierLibrary: # ИЗМЕНЕНО: Унифицированное имя
        """Создает новый модификатор."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            new_modifier = ModifierLibrary(**data)
            session.add(new_modifier)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Модификатор '{new_modifier.modifier_code}' создан.")
                return new_modifier
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании модификатора '{data.get('modifier_code', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Модификатор с таким кодом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании модификатора: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: str) -> Optional[ModifierLibrary]: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Получает модификатор по его коду (modifier_code)."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(ModifierLibrary).where(ModifierLibrary.modifier_code == id) # ИЗМЕНЕНО
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_all(self) -> List[ModifierLibrary]:
        """Получает все модификаторы из базы данных."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(ModifierLibrary)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[ModifierLibrary]: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Обновляет существующий модификатор по его коду (modifier_code)."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = update(ModifierLibrary).where(ModifierLibrary.modifier_code == id).values(**updates).returning(ModifierLibrary) # ИЗМЕНЕНО
            result = await session.execute(stmt) # ИЗМЕНЕНО
            updated_modifier = result.scalars().first()
            if updated_modifier:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Модификатор '{id}' обновлен.")
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Модификатор с кодом '{id}' не найден для обновления.")
            return updated_modifier

    async def delete(self, id: str) -> bool: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Удаляет модификатор по его коду (modifier_code)."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = delete(ModifierLibrary).where(ModifierLibrary.modifier_code == id) # ИЗМЕНЕНО
            result = await session.execute(stmt) # ИЗМЕНЕНО
            if result.rowcount > 0:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Модификатор '{id}' удален.")
                return True
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Модификатор '{id}' не найден для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> ModifierLibrary: # ИЗМЕНЕНО: Унифицированное имя
        """Создает или обновляет модификатор, используя UPSERT."""
        modifier_code = data.get("modifier_code")
        if not modifier_code:
            raise ValueError("Modifier code must be provided for upsert operation.")

        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
                insert_stmt = pg_insert(ModifierLibrary).values(**data)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[ModifierLibrary.modifier_code],
                    set_={
                        "name": insert_stmt.excluded.name,
                        "effect_description": insert_stmt.excluded.effect_description,
                        "value_tiers": insert_stmt.excluded.value_tiers, # ИЗМЕНЕНО: Исправлено на правильное имя поля
                        "randomization_range": insert_stmt.excluded.randomization_range, # ИЗМЕНЕНО: Исправлено на правильное имя поля
                        # Удалены: modifier_type, value, application_rules, т.к. их нет в ORM модели ModifierLibrary
                    }
                ).returning(ModifierLibrary)

                result = await session.execute(on_conflict_stmt) # ИЗМЕНЕНО
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit

                upserted_modifier = result.scalar_one_or_none()
                if not upserted_modifier:
                    raise RuntimeError("UPSERT модификатора не вернул объект.")
                logger.info(f"Модификатор '{modifier_code}' успешно добавлен/обновлен.")
                return upserted_modifier
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT модификатора '{modifier_code}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении модификатора: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT модификатора '{modifier_code}': {e}", exc_info=True)
                raise
    
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # ДОБАВЛЕНО: Унифицированное имя
        """Массово создает или обновляет модификаторы."""
        if not data_list:
            logger.info("Пустой список данных для ModifierLibrary upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
                updatable_fields = [
                    "name", "effect_description", "value_tiers", "randomization_range"
                ]
                set_clause = {field: getattr(pg_insert(ModifierLibrary).excluded, field) for field in updatable_fields}

                insert_stmt = pg_insert(ModifierLibrary).values(data_list)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[ModifierLibrary.modifier_code],
                    set_=set_clause
                )
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} модификаторов.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT модификаторов: {e}", exc_info=True)
                raise