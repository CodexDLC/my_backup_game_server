# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/active_game_data/used_character_archive_repository_impl.py

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

# Убедитесь, что путь к вашей модели UsedCharacterArchive корректен
from game_server.database.models.models import UsedCharacterArchive

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.interfaces_active_game_data import IUsedCharacterArchiveRepository
# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class UsedCharacterArchiveRepositoryImpl(IUsedCharacterArchiveRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью UsedCharacterArchive.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM (асинхронный).
    """
    def __init__(self, db_session: AsyncSession): # <--- ИЗМЕНЕНО: Конструктор для db_session
        self.db_session = db_session

    async def create_entry(self, original_pool_id: int, linked_entity_id: int, activation_type: str, linked_account_id: Optional[int] = None, simplified_pool_data: Optional[Dict[str, Any]] = None) -> UsedCharacterArchive:
        """CREATE: Создает новую запись в архиве."""
        archive_entry = UsedCharacterArchive(
            original_pool_id=original_pool_id,
            linked_entity_id=linked_entity_id,
            activation_type=activation_type,
            linked_account_id=linked_account_id,
            simplified_pool_data=simplified_pool_data or {}
        )
        self.db_session.add(archive_entry)
        try:
            await self.db_session.flush() # <--- ИЗМЕНЕНО: await flush
            logger.info(f"Запись архива (Pool ID: {original_pool_id}, Entity ID: {linked_entity_id}) создана в сессии.")
            return archive_entry
        except Exception as e:
            await self.db_session.rollback() # Откат при ошибке
            logger.error(f"Ошибка при создании записи архива: {e}", exc_info=True)
            raise

    async def get_entry_by_id(self, archive_id: int) -> Optional[UsedCharacterArchive]:
        """READ: Находит запись в архиве по её ID."""
        stmt = select(UsedCharacterArchive).where(UsedCharacterArchive.archive_id == archive_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def update_status(self, archive_id: int, new_status: str) -> Optional[UsedCharacterArchive]:
        """UPDATE: Обновляет статус жизненного цикла записи."""
        stmt = update(UsedCharacterArchive).where(UsedCharacterArchive.archive_id == archive_id).values(
            lifecycle_status=new_status
        ).returning(UsedCharacterArchive)
        result = await self.db_session.execute(stmt)
        updated_entry = result.scalars().first()
        if updated_entry:
            await self.db_session.flush()
            logger.info(f"Статус записи архива (ID: {archive_id}) обновлен на '{new_status}' в сессии.")
            return updated_entry
        else:
            logger.warning(f"Запись архива с ID {archive_id} не найдена для обновления статуса.")
            return None

    async def delete_entry(self, archive_id: int) -> bool:
        """DELETE: Удаляет запись из архива."""
        stmt = delete(UsedCharacterArchive).where(UsedCharacterArchive.archive_id == archive_id)
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0:
            await self.db_session.flush()
            logger.info(f"Запись архива (ID: {archive_id}) помечена для удаления в сессии.")
            return True
        else:
            logger.warning(f"Запись архива с ID {archive_id} не найдена для удаления.")
            return False