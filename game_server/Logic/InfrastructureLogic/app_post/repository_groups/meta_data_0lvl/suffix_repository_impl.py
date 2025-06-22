# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/suffix_repository_impl.py

import logging
from typing import List, Dict, Any, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound # Добавлено NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Suffix

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ISuffixRepository

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class SuffixRepositoryImpl(ISuffixRepository):
    """
    Репозиторий для управления объектами Suffix в базе данных (асинхронный).
    """
    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> Suffix: # ИЗМЕНЕНО: Унифицированное имя
        """Создает новый суффикс."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            new_suffix = Suffix(**data)
            session.add(new_suffix)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Суффикс '{new_suffix.suffix_code}' создан.")
                return new_suffix
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании суффикса '{data.get('suffix_code', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Суффикс с таким кодом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании суффикса: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: str) -> Optional[Suffix]: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Получает суффикс по его коду (suffix_code)."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(Suffix).where(Suffix.suffix_code == id) # ИЗМЕНЕНО
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_all(self) -> List[Suffix]:
        """Получает все суффиксы из базы данных."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(Suffix)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def get_suffixes_by_group(self, group: str) -> List[Suffix]:
        """Получает суффиксы, отфильтрованные по группе."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(Suffix).where(Suffix.group == group)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Suffix]: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Обновляет существующий суффикс по его коду (suffix_code)."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = update(Suffix).where(Suffix.suffix_code == id).values(**updates).returning(Suffix) # ИЗМЕНЕНО
            result = await session.execute(stmt) # ИЗМЕНЕНО
            updated_suffix = result.scalars().first()
            if updated_suffix:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Суффикс '{id}' обновлен.")
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Суффикс с кодом '{id}' не найден для обновления.")
            return updated_suffix

    async def delete(self, id: str) -> bool: # ИЗМЕНЕНО: Унифицированное имя, PK - str
        """Удаляет суффикс по его коду (suffix_code)."""
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = delete(Suffix).where(Suffix.suffix_code == id) # ИЗМЕНЕНО
            result = await session.execute(stmt) # ИЗМЕНЕНО
            if result.rowcount > 0:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Суффикс '{id}' удален.")
                return True
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Суффикс '{id}' не найден для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> Suffix: # ИЗМЕНЕНО: Унифицированное имя
        """Создает или обновляет суффикс, используя UPSERT."""
        suffix_code = data.get("suffix_code")
        if not suffix_code:
            raise ValueError("Suffix code must be provided for upsert operation.")

        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
                insert_stmt = pg_insert(Suffix).values(**data)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[Suffix.suffix_code],
                    set_={
                        "fragment": insert_stmt.excluded.fragment,
                        "group": insert_stmt.excluded.group,
                        "modifiers": insert_stmt.excluded.modifiers,
                    }
                ).returning(Suffix)

                result = await session.execute(on_conflict_stmt) # ИЗМЕНЕНО
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit

                upserted_suffix = result.scalar_one_or_none()
                if not upserted_suffix:
                    raise RuntimeError("UPSERT суффикса не вернул объект.")
                logger.info(f"Суффикс '{suffix_code}' успешно добавлен/обновлен.")
                return upserted_suffix
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT суффикса '{suffix_code}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении суффикса: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT суффикса '{suffix_code}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # ДОБАВЛЕНО: Унифицированное имя
        """Массово создает или обновляет суффиксы."""
        if not data_list:
            logger.info("Пустой список данных для Suffix upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
                updatable_fields = [
                    "fragment", "group", "modifiers"
                ]
                set_clause = {field: getattr(pg_insert(Suffix).excluded, field) for field in updatable_fields}

                insert_stmt = pg_insert(Suffix).values(data_list)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[Suffix.suffix_code],
                    set_=set_clause
                )
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} суффиксов.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT суффиксов: {e}", exc_info=True)
                raise