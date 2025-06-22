# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/state_entity_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func # ДОБАВЛЕНО func
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import StateEntity
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


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

    async def upsert(self, entity_data: Dict[str, Any]) -> StateEntity:
        """
        Создает или обновляет сущность состояния мира. Использует access_code как PK для ON CONFLICT.
        Соответствует абстрактному методу 'upsert'.
        """
        access_code = entity_data.get("access_code")
        if not access_code:
            raise ValueError("Access code must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
                # Список полей, которые можно обновлять. created_at не должен здесь быть.
                updatable_fields = [
                    "code_name",
                    "ui_type",
                    "description",
                    "is_active",
                ]

                # Фильтруем entity_data, чтобы не включать created_at в values(),
                # если оно не было явно предоставлено.
                # Также гарантируем, что 'access_code' всегда будет в values
                values_to_insert = {k: v for k, v in entity_data.items() if k != "created_at"}
                if "access_code" not in values_to_insert:
                    values_to_insert["access_code"] = access_code # Убедимся, что PK есть

                insert_stmt = pg_insert(StateEntity).values(**values_to_insert) # <--- ИЗМЕНЕНО: используем filtered dict

                # Определяем, какие поля обновлять при конфликте.
                # created_at не должно обновляться. updated_at (если есть) можно обновить через func.now()
                set_clause = {}
                for field in updatable_fields:
                    if field in insert_stmt.excluded: # Проверяем, что поле есть в данных для вставки
                        set_clause[field] = getattr(insert_stmt.excluded, field)

                # Добавляем updated_at, если оно есть в модели и должно обновляться автоматически
                # Проверяем модель StateEntity: updated_at там нет, но если бы было,
                # можно было бы добавить `updated_at=func.now()` сюда.
                # В StateEntity есть created_at с default.
                #
                # Ключевой момент: в models.py:
                # created_at: Mapped[datetime] = mapped_column(DateTime(True), default=lambda: datetime.now(timezone.utc))
                # Этот DEFAULT сработает ПРИ ВСТАВКЕ, если created_at не передан.
                # При ON CONFLICT DO UPDATE, мы не должны трогать created_at,
                # оно уже должно быть установлено при первой вставке.
                #
                # Убедимся, что set_clause не содержит created_at
                # И оно не должно быть в updatable_fields
                # set_={'data_hash': new_hash} # Это из DataVersion, здесь нужно свои поля.
                
                # Добавим created_at в excluded, чтобы убедиться, что оно не будет обновлено.
                # set_={k: getattr(insert_stmt.excluded, k) for k in updatable_fields}
                # Это уже было так, как мы перечислили updatable_fields.
                
                # final_set_clause = {
                #     "code_name": insert_stmt.excluded.code_name,
                #     "ui_type": insert_stmt.excluded.ui_type,
                #     "description": insert_stmt.excluded.description,
                #     "is_active": insert_stmt.excluded.is_active,
                # }

                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[StateEntity.access_code],
                    set_=set_clause # <--- ИЗМЕНЕНО: Используем динамически сгенерированный set_clause
                ).returning(StateEntity)

                result = await session.execute(upsert_stmt)
                await session.commit()
                upserted_entity = result.scalar_one_or_none()
                if not upserted_entity:
                    raise RuntimeError("UPSERT StateEntity не вернул объект.")
                logger.info(f"StateEntity '{access_code}' успешно добавлен/обновлен.")
                return upserted_entity
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT StateEntity '{access_code}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении StateEntity: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT StateEntity '{access_code}': {e}", exc_info=True)
                raise