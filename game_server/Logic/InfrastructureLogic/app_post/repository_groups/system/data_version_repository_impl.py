# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/system/data_version_repository_impl.py

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository
from game_server.database.models.models import DataVersion

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class DataVersionRepositoryImpl(IDataVersionRepository):
    """
    Репозиторий для работы с версиями данных в таблице DataVersion.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_initial_version(self, table_name: str, initial_hash: str) -> DataVersion:
        new_version = DataVersion(table_name=table_name, data_hash=initial_hash)
        self._session.add(new_version)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Создана начальная версия для '{table_name}': {initial_hash[:8]}... в сессии.")
        return new_version

    async def get_current_version(self, table_name: str) -> Optional[str]:
        stmt = fselect(DataVersion.data_hash).where(DataVersion.table_name == table_name)
        result = await self._session.execute(stmt)
        version_hash = result.scalar_one_or_none()
        return version_hash

    async def update_version(self, table_name: str, new_hash: str) -> DataVersion:
        return await self.upsert_version(table_name, new_hash)

    async def upsert_version(self, table_name: str, new_hash: str) -> DataVersion:
        insert_stmt = pg_insert(DataVersion).values(
            table_name=table_name,
            data_hash=new_hash
        )
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['table_name'],
            set_={'data_hash': new_hash}
        ).returning(DataVersion)

        result = await self._session.execute(upsert_stmt)
        updated_entity = result.scalar_one()
        await self._session.flush() # flush, но НЕ commit

        logger.debug(f"Версия для '{table_name}' в БД обновлена/создана: {updated_entity.data_hash[:8]}... в сессии.")
        return updated_entity
