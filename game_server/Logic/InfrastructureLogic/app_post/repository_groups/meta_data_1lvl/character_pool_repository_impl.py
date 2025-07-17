# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_1lvl/character_pool_repository_impl.py

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func as sql_func

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.database.models.models import CharacterPool


# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class CharacterPoolRepositoryImpl(ICharacterPoolRepository):
    """
    Репозиторий для выполнения асинхронных CRUD-операций над сущностью CharacterPool.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """

    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, character_data: Dict[str, Any]) -> CharacterPool:
        """
        Создает новую запись CharacterPool в рамках переданной сессии.
        """
        if 'character_pool_id' in character_data and character_data['character_pool_id'] is None:
            del character_data['character_pool_id']

        new_character = CharacterPool(**character_data)
        self._session.add(new_character)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Запись CharacterPool (ID: {new_character.character_pool_id if hasattr(new_character, 'character_pool_id') else 'N/A'}) добавлена в сессию.")
        return new_character

    async def upsert(self, character_data: Dict[str, Any]) -> CharacterPool:
        """
        Создает или обновляет запись CharacterPool, используя upsert (INSERT ON CONFLICT DO UPDATE) в рамках переданной сессии.
        """
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

        result = await self._session.execute(on_conflict_stmt)
        updated_or_inserted_character = result.scalar_one_or_none()
        await self._session.flush() # flush, но НЕ commit
        if not updated_or_inserted_character:
            raise RuntimeError("UPSERT CharacterPool не вернул объект.")
        logger.info(f"Запись CharacterPool (ID: {updated_or_inserted_character.character_pool_id}) успешно добавлена/обновлена в сессии.")
        return updated_or_inserted_character

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает или обновляет записи CharacterPool в рамках переданной сессии.
        Возвращает количество затронутых строк.
        """
        if not data_list:
            return 0

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

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        affected_rows = result.rowcount
        logger.info(f"Массовый upsert CharacterPool затронул {affected_rows} строк в сессии.")
        return affected_rows

    async def get_by_id(self, id: int) -> Optional[CharacterPool]:
        """
        Получает запись CharacterPool по её идентификатору в рамках переданной сессии.
        """
        stmt = fselect(CharacterPool).where(CharacterPool.character_pool_id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CharacterPool]:
        """
        Получает список записей CharacterPool с возможностью фильтрации, смещения и лимита в рамках переданной сессии.
        """
        stmt = fselect(CharacterPool)
        if filters:
            for key, value in filters.items():
                if hasattr(CharacterPool, key):
                    stmt = stmt.where(getattr(CharacterPool, key) == value)

        stmt = stmt.offset(offset).limit(limit).order_by(CharacterPool.character_pool_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, update_data: Dict[str, Any]) -> Optional[CharacterPool]:
        """
        Обновляет запись CharacterPool по её идентификатору в рамках переданной сессии.
        """
        if not update_data:
            return await self.get_by_id(id)

        stmt = (
            update(CharacterPool)
            .where(CharacterPool.character_pool_id == id)
            .values(**update_data)
            .returning(CharacterPool)
        )
        result = await self._session.execute(stmt)
        updated_character = result.scalar_one_or_none()
        if updated_character:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Запись CharacterPool (ID: {id}) обновлена в сессии.")
        else:
            logger.warning(f"Запись CharacterPool (ID: {id}) не найдена для обновления.")
        return updated_character

    async def delete(self, id: int) -> bool:
        """
        Удаляет запись CharacterPool по её идентификатору в рамках переданной сессии.
        """
        stmt = delete(CharacterPool).where(CharacterPool.character_pool_id == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Запись CharacterPool (ID: {id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Запись CharacterPool (ID: {id}) не найдена для удаления.")
            return False

    async def get_all(self) -> List[CharacterPool]:
        """
        Получает все записи из таблицы CharacterPool в рамках переданной сессии.
        Этот метод соответствует требованию интерфейса.
        """
        return await self.get_all_characters()

    async def find_one_available_and_lock(self) -> Optional[CharacterPool]:
        """
        Находит одну доступную для выдачи запись в пуле и атомарно блокирует ее
        на уровне БД, чтобы избежать гонки запросов, в рамках переданной сессии.
        """
        stmt = (
            fselect(CharacterPool)
            .where(CharacterPool.status == 'available')
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def delete_character(self, character: CharacterPool) -> bool:
        """Удаляет переданный объект CharacterPool из сессии в рамках переданной сессии."""
        if not character:
            logger.warning("Попытка удалить пустой объект CharacterPool.")
            return False
        await self._session.delete(character)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Объект CharacterPool (ID: {character.character_pool_id if hasattr(character, 'character_pool_id') else 'N/A'}) помечен для удаления в сессии.")
        return True

    async def get_all_characters(self) -> List[CharacterPool]:
        """
        Получает все записи из таблицы CharacterPool в рамках переданной сессии.
        """
        stmt = fselect(CharacterPool).order_by(CharacterPool.character_pool_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_random_sample(self, limit: int) -> List[Tuple[int, int]]:
        """
        Получает случайную выборку (ID, rarity_score) из доступных шаблонов в рамках переданной сессии.
        """
        stmt = (
            fselect(CharacterPool.character_pool_id, CharacterPool.rarity_score)
            .where(CharacterPool.status == 'available')
            .order_by(sql_func.random())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.fetchall()

    async def get_full_template_by_id(self, pool_id: int) -> Optional[CharacterPool]:
        """Получает полный шаблон персонажа по ID в рамках переданной сессии."""
        stmt = fselect(CharacterPool).where(CharacterPool.character_pool_id == pool_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_template_by_id(self, pool_id: int) -> bool:
        """Удаляет шаблон по ID в рамках переданной сессии. Возвращает True в случае успеха."""
        stmt = delete(CharacterPool).where(CharacterPool.character_pool_id == pool_id)
        result = await self._session.execute(stmt)
        # В транзакционной логике мы проверяем rowcount, чтобы убедиться, что удаление произошло
        return result.rowcount > 0
