# game_server/Logic/InfrastructureLogic/app_post/repository_groups/active_game_data/used_character_archive_repository_impl.py

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

# Импорт моделей и интерфейса
from game_server.database.models.models import UsedCharacterArchive
from .interfaces_active_game_data import IUsedCharacterArchiveRepository
from game_server.config.logging.logging_setup import app_logger as logger


class UsedCharacterArchiveRepositoryImpl(IUsedCharacterArchiveRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью UsedCharacterArchive.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимает активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_archive_record(
        self,
        original_pool_id: int,
        linked_entity_id: int,
        activation_type: str,
        lifecycle_status: str, # <--- ДОБАВЬТЕ ЭТО
        linked_account_id: Optional[int],
        simplified_pool_data: Optional[Dict[str, Any]]
    ) -> UsedCharacterArchive:
        # Ваша логика создания записи в БД.
        # Пример (если у вас есть модель UsedCharacterArchive):
        new_archive_entry = UsedCharacterArchive(
            original_pool_id=original_pool_id,
            linked_entity_id=linked_entity_id,
            activation_type=activation_type,
            lifecycle_status=lifecycle_status, # <--- ИСПОЛЬЗУЙТЕ ЭТО
            linked_account_id=linked_account_id,
            simplified_pool_data=simplified_pool_data
        )
        self._session.add(new_archive_entry)
        await self._session.flush()
        return new_archive_entry

    async def get_entry_by_id(self, archive_id: int) -> Optional[UsedCharacterArchive]:
        """READ: Находит запись в архиве по её ID."""
        stmt = select(UsedCharacterArchive).where(UsedCharacterArchive.archive_id == archive_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def update_status(self, archive_id: int, new_status: str) -> Optional[UsedCharacterArchive]:
        """UPDATE: Обновляет статус жизненного цикла записи."""
        stmt = update(UsedCharacterArchive).where(UsedCharacterArchive.archive_id == archive_id).values(
            lifecycle_status=new_status
        ).returning(UsedCharacterArchive)
        result = await self._session.execute(stmt)
        updated_entry = result.scalars().first()
        await self._session.flush() # flush, но НЕ commit
        if updated_entry:
            logger.info(f"Статус записи архива (ID: {archive_id}) обновлен на '{new_status}' в сессии.")
        return updated_entry

    async def delete_entry(self, archive_id: int) -> bool:
        """DELETE: Удаляет запись из архива."""
        stmt = delete(UsedCharacterArchive).where(UsedCharacterArchive.archive_id == archive_id)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        if result.rowcount > 0:
            logger.info(f"Запись архива (ID: {archive_id}) помечена для удаления в сессии.")
            return True
        return False
