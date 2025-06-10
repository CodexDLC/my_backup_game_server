from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import EquippedItems, Inventory




class EquippedItemsManager:
    """Менеджер для работы с `equipped_items` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def equip_item(self, character_id: int, equipped_data: dict):
        """Экипировать предмет персонажу."""
        item = EquippedItems(character_id=character_id, **equipped_data)
        self.db_session.add(item)
        await self.db_session.commit()
        return {"status": "success", "message": f"Предмет `{equipped_data['slot']}` экипирован персонажу `{character_id}`"}

    async def get_equipped_items(self, character_id: int):
        """Получение экипированных предметов персонажа."""
        query = select(EquippedItems).where(EquippedItems.character_id == character_id)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()
        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Предметы не найдены"}

    async def update_equipped_item(self, character_id: int, equipped_data: dict):
        """Обновление экипированного предмета."""
        query = select(EquippedItems).where(EquippedItems.character_id == character_id)
        result = await self.db_session.execute(query)
        item = result.scalar()

        if item:
            for key, value in equipped_data.items():
                setattr(item, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Экипировка `{character_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def unequip_item(self, character_id: int):
        """Удаление экипировки персонажа."""
        query = select(EquippedItems).where(EquippedItems.character_id == character_id)
        result = await self.db_session.execute(query)
        item = result.scalar()

        if item:
            await self.db_session.delete(item)
            await self.db_session.commit()
            return {"status": "success", "message": f"Экипировка `{character_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}
    


class InventoryManager:
    """Менеджер для работы с `inventory` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_item(self, inventory_id: int, inventory_data: dict):
        """Добавление нового предмета в инвентарь."""
        item = Inventory(inventory_id=inventory_id, **inventory_data)
        self.db_session.add(item)
        await self.db_session.commit()
        return {"status": "success", "message": f"Предмет `{inventory_data['item_id']}` добавлен в инвентарь персонажа `{inventory_data['character_id']}`"}

    async def get_item(self, inventory_id: int):
        """Получение предмета из инвентаря по ID."""
        query = select(Inventory).where(Inventory.inventory_id == inventory_id)
        result = await self.db_session.execute(query)
        item = result.scalar()
        return {"status": "found", "data": item.__dict__} if item else {"status": "error", "message": "Предмет в инвентаре не найден"}

    async def update_item(self, inventory_id: int, inventory_data: dict):
        """Обновление предмета в инвентаре."""
        query = select(Inventory).where(Inventory.inventory_id == inventory_id)
        result = await self.db_session.execute(query)
        item = result.scalar()

        if item:
            for key, value in inventory_data.items():
                setattr(item, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Инвентарь `{inventory_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def remove_item(self, inventory_id: int):
        """Удаление предмета из инвентаря."""
        query = select(Inventory).where(Inventory.inventory_id == inventory_id)
        result = await self.db_session.execute(query)
        item = result.scalar()

        if item:
            await self.db_session.delete(item)
            await self.db_session.commit()
            return {"status": "success", "message": f"Предмет `{inventory_id}` удалён из инвентаря"}
        return {"status": "error", "message": "Запись не найдена"}