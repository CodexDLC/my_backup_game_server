# game_server\Logic\ORM_LOGIC\managers\orm_accessory_templates.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import AccessoryTemplates, WeaponTemplates

class AccessoryTemplatesManager:
    """Менеджер для работы с `accessory_templates` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_accessory(self, accessory_id: int, accessory_data: dict):
        """Добавление нового аксессуара."""
        accessory = AccessoryTemplates(id=accessory_id, **accessory_data)
        self.db_session.add(accessory)
        await self.db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_data['name']}` добавлен"}

    async def get_accessory(self, accessory_id: int):
        """Получение аксессуара по ID."""
        query = select(AccessoryTemplates).where(AccessoryTemplates.id == accessory_id)
        result = await self.db_session.execute(query)
        accessory = result.scalar()
        return {"status": "found", "data": accessory.__dict__} if accessory else {"status": "error", "message": "Аксессуар не найден"}

    async def update_accessory(self, accessory_id: int, accessory_data: dict):
        """Обновление данных аксессуара."""
        query = select(AccessoryTemplates).where(AccessoryTemplates.id == accessory_id)
        result = await self.db_session.execute(query)
        accessory = result.scalar()

        if accessory:
            for key, value in accessory_data.items():
                setattr(accessory, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Аксессуар `{accessory_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_accessory(self, accessory_id: int):
        """Удаление аксессуара."""
        query = select(AccessoryTemplates).where(AccessoryTemplates.id == accessory_id)
        result = await self.db_session.execute(query)
        accessory = result.scalar()

        if accessory:
            await self.db_session.delete(accessory)
            await self.db_session.commit()
            return {"status": "success", "message": f"Аксессуар `{accessory_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}


class AccessoryTemplatesManager:
    """Менеджер для работы с `accessory_templates` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_accessory(self, accessory_id: int, accessory_data: dict):
        """Добавление нового аксессуара."""
        accessory = AccessoryTemplates(id=accessory_id, **accessory_data)
        self.db_session.add(accessory)
        await self.db_session.commit()
        return {"status": "success", "message": f"Аксессуар `{accessory_data['name']}` добавлен"}

    async def get_accessory(self, accessory_id: int):
        """Получение аксессуара по ID."""
        query = select(AccessoryTemplates).where(AccessoryTemplates.id == accessory_id)
        result = await self.db_session.execute(query)
        accessory = result.scalar()
        return {"status": "found", "data": accessory.__dict__} if accessory else {"status": "error", "message": "Аксессуар не найден"}

    async def update_accessory(self, accessory_id: int, accessory_data: dict):
        """Обновление данных аксессуара."""
        query = select(AccessoryTemplates).where(AccessoryTemplates.id == accessory_id)
        result = await self.db_session.execute(query)
        accessory = result.scalar()

        if accessory:
            for key, value in accessory_data.items():
                setattr(accessory, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Аксессуар `{accessory_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_accessory(self, accessory_id: int):
        """Удаление аксессуара."""
        query = select(AccessoryTemplates).where(AccessoryTemplates.id == accessory_id)
        result = await self.db_session.execute(query)
        accessory = result.scalar()

        if accessory:
            await self.db_session.delete(accessory)
            await self.db_session.commit()
            return {"status": "success", "message": f"Аксессуар `{accessory_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}


class WeaponTemplatesManager:
    """Менеджер для работы с `weapon_templates` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_weapon(self, weapon_id: int, weapon_data: dict):
        """Добавление нового оружия."""
        weapon = WeaponTemplates(id=weapon_id, **weapon_data)
        self.db_session.add(weapon)
        await self.db_session.commit()
        return {"status": "success", "message": f"Оружие `{weapon_data['name']}` добавлено"}

    async def get_weapon(self, weapon_id: int):
        """Получение оружия по ID."""
        query = select(WeaponTemplates).where(WeaponTemplates.id == weapon_id)
        result = await self.db_session.execute(query)
        weapon = result.scalar()
        return {"status": "found", "data": weapon.__dict__} if weapon else {"status": "error", "message": "Оружие не найдено"}

    async def update_weapon(self, weapon_id: int, weapon_data: dict):
        """Обновление данных оружия."""
        query = select(WeaponTemplates).where(WeaponTemplates.id == weapon_id)
        result = await self.db_session.execute(query)
        weapon = result.scalar()

        if weapon:
            for key, value in weapon_data.items():
                setattr(weapon, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Оружие `{weapon_id}` обновлено"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_weapon(self, weapon_id: int):
        """Удаление оружия."""
        query = select(WeaponTemplates).where(WeaponTemplates.id == weapon_id)
        result = await self.db_session.execute(query)
        weapon = result.scalar()

        if weapon:
            await self.db_session.delete(weapon)
            await self.db_session.commit()
            return {"status": "success", "message": f"Оружие `{weapon_id}` удалено"}
        return {"status": "error", "message": "Запись не найдена"}



