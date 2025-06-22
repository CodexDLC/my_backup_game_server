# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_1lvl/character_pool_repository_impl.py

import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Type # Добавлен Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError


from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.database.models.models import CharacterPool


# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class CharacterPoolRepositoryImpl(ICharacterPoolRepository):
    """
    Репозиторий для выполнения асинхронных CRUD-операций над сущностью CharacterPool.
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """

    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, character_data: Dict[str, Any]) -> CharacterPool:
        """
        Создает новую запись CharacterPool в базе данных.
        """
        if 'character_pool_id' in character_data and character_data['character_pool_id'] is None:
            del character_data['character_pool_id']

        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            new_character = CharacterPool(**character_data)
            session.add(new_character)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Запись CharacterPool (ID: {new_character.character_pool_id if hasattr(new_character, 'character_pool_id') else 'N/A'}) создана в сессии.")
                return new_character
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании записи CharacterPool: {e.orig}", exc_info=True)
                raise ValueError(f"Запись CharacterPool уже существует или данные некорректны.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании записи CharacterPool: {e}", exc_info=True)
                raise

    async def upsert(self, character_data: Dict[str, Any]) -> CharacterPool:
        """
        Создает или обновляет запись CharacterPool, используя upsert (INSERT ON CONFLICT DO UPDATE).
        """
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            try:
                insert_stmt = pg_insert(CharacterPool).values(**character_data)

                updatable_fields = {
                    k: insert_stmt.excluded[k]
                    for k in CharacterPool.__table__.columns.keys()
                    if k != 'character_pool_id'
                }

                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[CharacterPool.character_pool_id],
                    set_=updatable_fields
                ).returning(CharacterPool)

                result = await session.execute(on_conflict_stmt) # ИСПРАВЛЕНО
                updated_or_inserted_character = result.scalar_one_or_none()
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                if not updated_or_inserted_character:
                    raise RuntimeError("UPSERT CharacterPool не вернул объект.")
                logger.info(f"Запись CharacterPool (ID: {updated_or_inserted_character.character_pool_id}) успешно добавлена/обновлена в сессии.")
                return updated_or_inserted_character
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT записи CharacterPool: {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении записи CharacterPool: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT записи CharacterPool: {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает или обновляет записи CharacterPool.
        Возвращает количество затронутых строк.
        """
        if not data_list:
            return 0

        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            try:
                insert_stmt = pg_insert(CharacterPool).values(data_list)

                updatable_fields = {
                    k: insert_stmt.excluded[k]
                    for k in CharacterPool.__table__.columns.keys()
                    if k not in ['character_pool_id']
                }

                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[CharacterPool.character_pool_id],
                    set_=updatable_fields
                )

                result = await session.execute(on_conflict_stmt) # ИСПРАВЛЕНО
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                affected_rows = result.rowcount
                logger.info(f"Массовый upsert CharacterPool затронул {affected_rows} строк.")
                return affected_rows
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при массовом UPSERT CharacterPool: {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при массовом сохранении CharacterPool: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при массовом UPSERT CharacterPool: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[CharacterPool]:
        """
        Получает запись CharacterPool по её идентификатору.
        """
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = fselect(CharacterPool).where(CharacterPool.character_pool_id == id)
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            return result.scalar_one_or_none()

    async def get_many(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CharacterPool]:
        """
        Получает список записей CharacterPool с возможностью фильтрации, смещения и лимита.
        """
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = fselect(CharacterPool)
            if filters:
                for key, value in filters.items():
                    if hasattr(CharacterPool, key):
                        stmt = stmt.where(getattr(CharacterPool, key) == value)

            stmt = stmt.offset(offset).limit(limit).order_by(CharacterPool.character_pool_id)
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            return list(result.scalars().all())

    async def update(self, id: int, update_data: Dict[str, Any]) -> Optional[CharacterPool]:
        """
        Обновляет запись CharacterPool по её идентификатору.
        """
        if not update_data:
            return await self.get_by_id(id)

        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = (
                update(CharacterPool)
                .where(CharacterPool.character_pool_id == id)
                .values(**update_data)
                .returning(CharacterPool)
            )
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            updated_character = result.scalar_one_or_none()
            if updated_character:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Запись CharacterPool (ID: {id}) обновлена в сессии.")
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Запись CharacterPool (ID: {id}) не найдена для обновления.")
            return updated_character

    async def delete(self, id: int) -> bool:
        """
        Удаляет запись CharacterPool по её идентификатору.
        """
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = delete(CharacterPool).where(CharacterPool.character_pool_id == id)
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            if result.rowcount > 0:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Запись CharacterPool (ID: {id}) помечена для удаления в сессии.")
                return True
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Запись CharacterPool (ID: {id}) не найдена для удаления.")
                return False

    async def get_all(self) -> List[CharacterPool]:
        """
        Получает все записи из таблицы CharacterPool.
        Этот метод соответствует требованию интерфейса.
        """
        return await self.get_all_characters()

    async def find_one_available_and_lock(self) -> Optional[CharacterPool]:
        """
        Находит одну доступную для выдачи запись в пуле и атомарно блокирует ее
        на уровне БД, чтобы избежать гонки запросов.
        """
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = (
                fselect(CharacterPool)
                .where(CharacterPool.status == 'available')
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            return result.scalars().first()

    async def delete_character(self, character: CharacterPool) -> bool:
        """Удаляет переданный объект CharacterPool из сессии."""
        if not character:
            logger.warning("Попытка удалить пустой объект CharacterPool.")
            return False
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            await session.delete(character) # ИСПРАВЛЕНО
            await session.flush()
            await session.commit() # ДОБАВЛЕНО commit
            logger.info(f"Объект CharacterPool (ID: {character.character_pool_id if hasattr(character, 'character_pool_id') else 'N/A'}) помечен для удаления в сессии.")
            return True

    async def get_all_characters(self) -> List[CharacterPool]:
        """
        Получает все записи из таблицы CharacterPool.
        """
        async with await self._get_session() as session: # ИСПРАВЛЕНО: Использование async with
            stmt = fselect(CharacterPool).order_by(CharacterPool.character_pool_id)
            result = await session.execute(stmt) # ИСПРАВЛЕНО
            return list(result.scalars().all())