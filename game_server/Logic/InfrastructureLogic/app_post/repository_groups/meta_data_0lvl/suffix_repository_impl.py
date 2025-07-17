# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/suffix_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Suffix

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ISuffixRepository

from game_server.config.logging.logging_setup import app_logger as logger


class SuffixRepositoryImpl(ISuffixRepository):
    """
    Репозиторий для управления объектами Suffix в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> Suffix:
        """Создает новый суффикс в рамках переданной сессии."""
        new_suffix = Suffix(**data)
        self._session.add(new_suffix)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Суффикс '{new_suffix.suffix_code}' добавлен в сессию.")
        return new_suffix

    async def get_by_id(self, id: str) -> Optional[Suffix]:
        """Получает суффикс по его коду (suffix_code) в рамках переданной сессии."""
        stmt = fselect(Suffix).where(Suffix.suffix_code == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Suffix]:
        """Получает все суффиксы из базы данных в рамках переданной сессии."""
        stmt = fselect(Suffix)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_suffixes_by_group(self, group: str) -> List[Suffix]:
        """Получает суффиксы, отфильтрованные по группе, в рамках переданной сессии."""
        stmt = fselect(Suffix).where(Suffix.group == group)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Suffix]:
        """Обновляет существующий суффикс по его коду (suffix_code) в рамках переданной сессии."""
        stmt = update(Suffix).where(Suffix.suffix_code == id).values(**updates).returning(Suffix)
        result = await self._session.execute(stmt)
        updated_suffix = result.scalars().first()
        if updated_suffix:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Суффикс '{id}' обновлен в сессии.")
        else:
            logger.warning(f"Суффикс с кодом '{id}' не найден для обновления.")
        return updated_suffix

    async def delete(self, id: str) -> bool:
        """Удаляет суффикс по его коду (suffix_code) в рамках переданной сессии."""
        stmt = delete(Suffix).where(Suffix.suffix_code == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Суффикс '{id}' помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Суффикс с кодом '{id}' не найден для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> Suffix:
        """Создает или обновляет суффикс, используя UPSERT в рамках переданной сессии."""
        suffix_code = data.get("suffix_code")
        if not suffix_code:
            raise ValueError("Suffix code must be provided for upsert operation.")

        insert_stmt = pg_insert(Suffix).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Suffix.suffix_code],
            set_={
                "fragment": insert_stmt.excluded.fragment,
                "group": insert_stmt.excluded.group,
                "modifiers": insert_stmt.excluded.modifiers,
            }
        ).returning(Suffix)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_suffix = result.scalar_one_or_none()
        if not upserted_suffix:
            raise RuntimeError("UPSERT суффикса не вернул объект.")
        logger.info(f"Суффикс '{suffix_code}' успешно добавлен/обновлен в сессии.")
        return upserted_suffix

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет суффиксы в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для Suffix upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "fragment", "group", "modifiers"
        ]
        set_clause = {field: getattr(pg_insert(Suffix).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(Suffix).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Suffix.suffix_code],
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} суффиксов в сессии.")
        return upserted_count
