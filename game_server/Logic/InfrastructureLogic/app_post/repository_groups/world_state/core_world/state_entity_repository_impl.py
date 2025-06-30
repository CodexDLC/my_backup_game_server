# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/state_entity_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import StateEntity
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository
from game_server.config.logging.logging_setup import app_logger as logger


class StateEntityRepositoryImpl(IStateEntityRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью StateEntity.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронно).
    Строго следует интерфейсу IStateEntityRepository, используя 'access_code' как PK.
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, entity_data: Dict[str, Any]) -> StateEntity:
        """
        Создает новую сущность состояния мира.
        Соответствует абстрактному методу 'create'.
        """
        async with await self._get_session() as session:
            new_entity = StateEntity(**entity_data)
            session.add(new_entity)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Сущность состояния мира (access_code: {new_entity.access_code}) создана.")
                return new_entity
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании сущности состояния мира (access_code: {entity_data.get('access_code')}): {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при создании сущности состояния мира: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании сущности состояния мира (access_code: {entity_data.get('access_code')}): {e}", exc_info=True)
                raise

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
        Получает сущность состояния мира по её уникальному access_code (PK).
        Соответствует абстрактному методу 'get_by_access_code'.
        """
        async with await self._get_session() as session:
            stmt = select(StateEntity).where(StateEntity.access_code == access_code)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[StateEntity]:
        """
        Получает все сущности состояния мира.
        Соответствует абстрактному методу 'get_all'.
        """
        async with await self._get_session() as session:
            stmt = select(StateEntity)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, access_code: str, updates: Dict[str, Any]) -> Optional[StateEntity]:
        """
        Обновляет сущность состояния мира по её access_code.
        Соответствует абстрактному методу 'update'.
        """
        async with await self._get_session() as session:
            try:
                stmt = update(StateEntity).where(StateEntity.access_code == access_code).values(**updates).returning(StateEntity)
                result = await session.execute(stmt)
                updated_entity = result.scalars().first()
                if updated_entity:
                    await session.commit()
                    logger.info(f"Сущность состояния мира (access_code: {access_code}) обновлена.")
                else:
                    await session.rollback()
                    logger.warning(f"Сущность состояния мира (access_code: {access_code}) не найдена для обновления.")
                return updated_entity
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при обновлении сущности состояния мира (access_code: {access_code}): {e}", exc_info=True)
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при обновлении сущности состояния мира (access_code: {access_code}): {e}", exc_info=True)
                raise

    async def delete(self, access_code: str) -> bool:
        """
        Удаляет сущность состояния мира по её access_code.
        Соответствует абстрактному методу 'delete'.
        """
        async with await self._get_session() as session:
            stmt = delete(StateEntity).where(StateEntity.access_code == access_code)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.commit()
                logger.info(f"Сущность состояния мира (access_code: {access_code}) удалена.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Сущность состояния мира (access_code: {access_code}) не найдена для удаления.")
                return False

    async def upsert(self, entity_data: Dict[str, Any]) -> Optional[StateEntity]:
        """
        Создает или обновляет сущность состояния мира. Использует access_code как PK для ON CONFLICT.
        Соответствует абстрактному методу 'upsert'.
        """
        access_code = entity_data.get("access_code")
        if not access_code:
            raise ValueError("Access code must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
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

                result = await session.execute(upsert_stmt)
                upserted_entity = result.scalar_one_or_none()
                await session.commit()
                if not upserted_entity:
                    await session.rollback() # Откатываем, если объект не вернулся
                    raise RuntimeError("UPSERT StateEntity не вернул объект.")
                logger.info(f"StateEntity '{access_code}' успешно добавлен/обновлен.")
                return upserted_entity
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT StateEntity '{access_code}': {e.orig}", exc_info=True)
                return None # Возвращаем None при ошибке целостности
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка SQLAlchemy при UPSERT StateEntity '{access_code}': {e}", exc_info=True)
                return None
            except Exception as e:
                await session.rollback()
                logger.critical(f"Непредвиденная ошибка при UPSERT StateEntity '{access_code}': {e}", exc_info=True)
                raise
