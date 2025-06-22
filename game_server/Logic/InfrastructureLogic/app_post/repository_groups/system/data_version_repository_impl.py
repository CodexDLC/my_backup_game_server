# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/system/data_version_repository_impl.py

import logging
from typing import Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, NoResultFound

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository
from game_server.database.models.models import DataVersion

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class DataVersionRepositoryImpl(IDataVersionRepository):
    """
    Репозиторий для работы с версиями данных в таблице DataVersion.
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create_initial_version(self, table_name: str, initial_hash: str) -> DataVersion:
        # ИЗМЕНЕНО: Добавлен await перед self._get_session()
        async with await self._get_session() as session: # <--- ИСПРАВЛЕНО
            new_version = DataVersion(table_name=table_name, data_hash=initial_hash)
            session.add(new_version)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Создана начальная версия для '{table_name}': {initial_hash[:8]}...")
                return new_version
            except IntegrityError:
                await session.rollback()
                logger.warning(f"Начальная версия для '{table_name}' уже существует. Попытка обновления.")
                return await self.upsert_version(table_name, initial_hash)
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка при создании начальной версии для '{table_name}': {e}", exc_info=True)
                raise

    async def get_current_version(self, table_name: str) -> Optional[str]:
        # ИЗМЕНЕНО: Добавлен await перед self._get_session()
        async with await self._get_session() as session: # <--- ИСПРАВЛЕНО
            try:
                stmt = fselect(DataVersion.data_hash).where(DataVersion.table_name == table_name)
                result = await session.execute(stmt)
                version_hash = result.scalar_one_or_none()
                return version_hash
            except Exception as e:
                logger.error(f"Ошибка при получении версии для '{table_name}': {e}", exc_info=True)
                raise

    async def update_version(self, table_name: str, new_hash: str) -> DataVersion:
        return await self.upsert_version(table_name, new_hash)

    async def upsert_version(self, table_name: str, new_hash: str) -> DataVersion:
        # ИЗМЕНЕНО: Добавлен await перед self._get_session()
        async with await self._get_session() as session: # <--- ИСПРАВЛЕНО
            try:
                insert_stmt = pg_insert(DataVersion).values(
                    table_name=table_name,
                    data_hash=new_hash
                )
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['table_name'],
                    set_={'data_hash': new_hash}
                ).returning(DataVersion)

                result = await session.execute(upsert_stmt)
                updated_entity = result.scalar_one()
                await session.flush()
                await session.commit()
                
                logger.debug(f"Версия для '{table_name}' в БД обновлена/создана: {updated_entity.data_hash[:8]}...")
                return updated_entity
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT версии для '{table_name}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении версии: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT версии для '{table_name}': {e}", exc_info=True)
                raise