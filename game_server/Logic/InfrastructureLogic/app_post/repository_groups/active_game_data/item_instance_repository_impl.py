# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/active_game_data/item_instance_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete

# Импорт вашей модели InstancedItem
from game_server.database.models.models import InstancedItem

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.interfaces_active_game_data import IItemInstanceRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class ItemInstanceRepositoryImpl(IItemInstanceRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью InstancedItem.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ

    async def create_item_instance(self, data: Dict[str, Any]) -> InstancedItem:
        """
        Создает новую запись экземпляра предмета в базе данных.
        :param data: Словарь с данными экземпляра.
        :return: Созданный объект InstancedItem.
        """
        new_instance = InstancedItem(**data)
        self.db_session.add(new_instance)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Экземпляр предмета (ID: {new_instance.instance_id if hasattr(new_instance, 'instance_id') else 'N/A'}) добавлен в сессию.")
        return new_instance

    async def get_item_instance_by_id(self, instance_id: int) -> Optional[InstancedItem]:
        """
        Получает экземпляр предмета по его ID.
        """
        stmt = select(InstancedItem).where(InstancedItem.instance_id == instance_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_items_by_owner(self, owner_id: int, owner_type: str, location_type: Optional[str] = None) -> List[InstancedItem]:
        """
        Получает все экземпляры предметов, принадлежащие определенному владельцу,
        опционально фильтруя по типу местоположения.
        """
        stmt = select(InstancedItem).where(
            InstancedItem.owner_id == owner_id,
            InstancedItem.owner_type == owner_type
        )
        if location_type:
            stmt = stmt.where(InstancedItem.location_type == location_type)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def update_item_instance(self, instance_id: int, updates: Dict[str, Any]) -> Optional[InstancedItem]:
        """
        Обновляет существующий экземпляр предмета по его ID.
        """
        stmt = update(InstancedItem).where(InstancedItem.instance_id == instance_id).values(**updates).returning(InstancedItem)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Экземпляр предмета (ID: {instance_id}) обновлен в сессии.")
        return result.scalars().first()

    async def delete_item_instance(self, instance_id: int) -> bool:
        """
        Удаляет экземпляр предмета по его ID.
        """
        stmt = delete(InstancedItem).where(InstancedItem.instance_id == instance_id)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Экземпляр предмета (ID: {instance_id}) помечен для удаления в сессии.")
        return result.rowcount > 0

    async def transfer_item_instance(self, instance_id: int, new_owner_id: int, new_owner_type: str, new_location_type: str, new_location_slot: Optional[str] = None) -> Optional[InstancedItem]:
        """
        Перемещает экземпляр предмета к новому владельцу или в новое местоположение.
        """
        stmt = update(InstancedItem).where(InstancedItem.instance_id == instance_id).values(
            owner_id=new_owner_id,
            owner_type=new_owner_type,
            location_type=new_location_type,
            location_slot=new_location_slot
        ).returning(InstancedItem)
        result = await self.db_session.execute(stmt)
        await self.db_session.flush() # flush, но НЕ commit
        logger.info(f"Экземпляр предмета (ID: {instance_id}) передан в сессии.")
        return result.scalars().first()
