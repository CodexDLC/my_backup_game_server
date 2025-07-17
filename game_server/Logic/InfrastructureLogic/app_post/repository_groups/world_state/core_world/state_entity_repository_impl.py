# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/state_entity_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import StateEntity
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository
from game_server.config.logging.logging_setup import app_logger as logger


class StateEntityRepositoryImpl(IStateEntityRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью StateEntity.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    Строго следует интерфейсу IStateEntityRepository, используя 'access_code' как PK.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, entity_data: Dict[str, Any]) -> StateEntity:
        """
        Создает новую сущность состояния мира в рамках переданной сессии.
        Соответствует абстрактному методу 'create'.
        """
        new_entity = StateEntity(**entity_data)
        self._session.add(new_entity)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Сущность состояния мира (access_code: {new_entity.access_code}) добавлена в сессию.")
        return new_entity

    async def get_by_id(self, entity_id: int) -> Optional[StateEntity]:
        """
        Получает сущность состояния мира по её ID.
        (ОСТОРОЖНО: ORM-модель StateEntity использует 'access_code' (str) как PK, а не 'id' (int).
        Этот метод в интерфейсе, но может вызвать путаницу. Возвращает None, т.к. нет int PK.)
        """
        logger.warning(f"Вызван get_by_id({entity_id}) для StateEntity, но ORM-модель использует 'access_code' (str) как PK. "
                        f"Этот метод не поддерживается для StateEntity. Используйте get_by_access_code вместо этого.")
        raise NotImplementedError(f"Поиск StateEntity по целочисленному ID '{entity_id}' не поддерживается, так как PK - 'access_code' (строка).")

    async def get_by_access_code(self, access_code: str) -> Optional[StateEntity]:
        """
        Получает сущность состояния мира по её уникальному access_code (PK) в рамках переданной сессии.
        Соответствует абстрактному методу 'get_by_access_code'.
        """
        stmt = select(StateEntity).where(StateEntity.access_code == access_code)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_all(self) -> List[StateEntity]:
        """
        Получает все сущности состояния мира из базы данных в рамках переданной сессии.
        Соответствует абстрактному методу 'get_all'.
        """
        stmt = select(StateEntity)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, access_code: str, updates: Dict[str, Any]) -> Optional[StateEntity]:
        """
        Обновляет сущность состояния мира по её access_code в рамках переданной сессии.
        Соответствует абстрактному методу 'update'.
        """
        stmt = update(StateEntity).where(StateEntity.access_code == access_code).values(**updates).returning(StateEntity)
        result = await self._session.execute(stmt)
        updated_entity = result.scalars().first()
        if updated_entity:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сущность состояния мира (access_code: {access_code}) обновлена в сессии.")
        else:
            logger.warning(f"Сущность состояния мира (access_code: {access_code}) не найдена для обновления.")
        return updated_entity

    async def delete(self, access_code: str) -> bool:
        """
        Удаляет сущность состояния мира по её access_code в рамках переданной сессии.
        Соответствует абстрактному методу 'delete'.
        """
        stmt = delete(StateEntity).where(StateEntity.access_code == access_code)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Сущность состояния мира (access_code: {access_code}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Сущность состояния мира (access_code: {access_code}) не найдена для удаления.")
            return False

    async def upsert(self, entity_data: Dict[str, Any]) -> Optional[StateEntity]:
        """
        Создает или обновляет сущность состояния мира в рамках переданной сессии. Использует access_code как PK для ON CONFLICT.
        Соответствует абстрактному методу 'upsert'.
        """
        access_code = entity_data.get("access_code")
        if not access_code:
            raise ValueError("Access code must be provided for upsert operation.")

        updatable_fields = [
            "code_name",
            "ui_type",
            "description",
            "is_active",
        ]

        # ИСПРАВЛЕНИЕ: Фильтруем entity_data, чтобы ИСКЛЮЧИТЬ 'id', 'created_at' И 'updated_at' из values().
        # created_at и updated_at имеют default/onupdate в модели, а id - это автоинкрементный PK.
        values_to_insert = {k: v for k, v in entity_data.items() if k not in ["created_at", "updated_at", "id"]}

        # Убедимся, что 'access_code' всегда будет в values, если вдруг его нет
        if "access_code" not in values_to_insert:
            values_to_insert["access_code"] = access_code

        insert_stmt = pg_insert(StateEntity).values(**values_to_insert)

        set_clause = {}
        for field in updatable_fields:
            if field in insert_stmt.excluded:
                set_clause[field] = getattr(insert_stmt.excluded, field)

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[StateEntity.access_code], # Конфликт по access_code
            set_=set_clause # Используем динамически сгенерированный set_clause
        ).returning(StateEntity)

        result = await self._session.execute(upsert_stmt)
        upserted_entity = result.scalar_one_or_none()
        await self._session.flush() # flush, но НЕ commit
        if not upserted_entity:
            raise RuntimeError("UPSERT StateEntity не вернул объект.")
        logger.info(f"StateEntity '{access_code}' успешно добавлен/обновлен в сессии.")
        return upserted_entity
