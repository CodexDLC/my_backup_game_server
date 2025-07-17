# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/modifier_library_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import ModifierLibrary

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IModifierLibraryRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class ModifierLibraryRepositoryImpl(IModifierLibraryRepository):
    """
    Репозиторий для управления объектами ModifierLibrary в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> ModifierLibrary:
        """Создает новый модификатор в рамках переданной сессии."""
        new_modifier = ModifierLibrary(**data)
        self._session.add(new_modifier)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Модификатор '{new_modifier.modifier_code}' добавлен в сессию.")
        return new_modifier

    async def get_by_id(self, id: str) -> Optional[ModifierLibrary]:
        """Получает модификатор по его коду (modifier_code) в рамках переданной сессии."""
        stmt = fselect(ModifierLibrary).where(ModifierLibrary.modifier_code == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[ModifierLibrary]:
        """Получает все модификаторы из базы данных в рамках переданной сессии."""
        stmt = fselect(ModifierLibrary)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[ModifierLibrary]:
        """Обновляет существующий модификатор по его коду (modifier_code) в рамках переданной сессии."""
        stmt = update(ModifierLibrary).where(ModifierLibrary.modifier_code == id).values(**updates).returning(ModifierLibrary)
        result = await self._session.execute(stmt)
        updated_modifier = result.scalars().first()
        if updated_modifier:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Модификатор '{id}' обновлен в сессии.")
        else:
            logger.warning(f"Модификатор с кодом '{id}' не найден для обновления.")
        return updated_modifier

    async def delete(self, id: str) -> bool:
        """Удаляет модификатор по его коду (modifier_code) в рамках переданной сессии."""
        stmt = delete(ModifierLibrary).where(ModifierLibrary.modifier_code == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Модификатор '{id}' помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Модификатор '{id}' не найден для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> ModifierLibrary:
        """Создает или обновляет модификатор, используя UPSERT в рамках переданной сессии."""
        modifier_code = data.get("modifier_code")
        if not modifier_code:
            raise ValueError("Modifier code must be provided for upsert operation.")

        insert_stmt = pg_insert(ModifierLibrary).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[ModifierLibrary.modifier_code],
            set_={
                "name": insert_stmt.excluded.name,
                "effect_description": insert_stmt.excluded.effect_description,
                "value_tiers": insert_stmt.excluded.value_tiers,
                "randomization_range": insert_stmt.excluded.randomization_range,
            }
        ).returning(ModifierLibrary)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_modifier = result.scalar_one_or_none()
        if not upserted_modifier:
            raise RuntimeError("UPSERT модификатора не вернул объект.")
        logger.info(f"Модификатор '{modifier_code}' успешно добавлен/обновлен в сессии.")
        return upserted_modifier

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет модификаторы в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для ModifierLibrary upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "name", "effect_description", "value_tiers", "randomization_range"
        ]
        set_clause = {field: getattr(pg_insert(ModifierLibrary).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(ModifierLibrary).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[ModifierLibrary.modifier_code],
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} модификаторов в сессии.")
        return upserted_count
