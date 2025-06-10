# game_server\Logic\ORM_LOGIC\managers\orm_worlds.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import Regions, Subregions, Worlds




class WorldsManager:
    """Менеджер для работы с `worlds` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_world(self, world_data: dict):
        """Добавление нового мира."""
        world = Worlds(**world_data)
        self.db_session.add(world)
        await self.db_session.commit()
        return {"status": "success", "message": f"Мир `{world_data['name']}` создан"}

    async def get_world(self, world_id: str):
        """Получение мира по ID."""
        query = select(Worlds).where(Worlds.id == world_id)
        result = await self.db_session.execute(query)
        world = result.scalar()
        return {"status": "found", "data": world.__dict__} if world else {"status": "error", "message": "Мир не найден"}

    async def update_world(self, world_id: str, world_data: dict):
        """Обновление данных мира."""
        query = select(Worlds).where(Worlds.id == world_id)
        result = await self.db_session.execute(query)
        world = result.scalar()

        if world:
            for key, value in world_data.items():
                setattr(world, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Мир `{world_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_world(self, world_id: str):
        """Удаление мира."""
        query = select(Worlds).where(Worlds.id == world_id)
        result = await self.db_session.execute(query)
        world = result.scalar()

        if world:
            await self.db_session.delete(world)
            await self.db_session.commit()
            return {"status": "success", "message": f"Мир `{world_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
    



class RegionsManager:
    """Менеджер для работы с `regions` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_region(self, region_data: dict):
        """Добавление нового региона."""
        region = Regions(**region_data)
        self.db_session.add(region)
        await self.db_session.commit()
        return {"status": "success", "message": f"Регион `{region_data['name']}` создан"}

    async def get_region(self, region_id: str):
        """Получение региона по ID."""
        query = select(Regions).where(Regions.id == region_id)
        result = await self.db_session.execute(query)
        region = result.scalar()
        return {"status": "found", "data": region.__dict__} if region else {"status": "error", "message": "Регион не найден"}

    async def update_region(self, region_id: str, region_data: dict):
        """Обновление данных региона."""
        query = select(Regions).where(Regions.id == region_id)
        result = await self.db_session.execute(query)
        region = result.scalar()

        if region:
            for key, value in region_data.items():
                setattr(region, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Регион `{region_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_region(self, region_id: str):
        """Удаление региона."""
        query = select(Regions).where(Regions.id == region_id)
        result = await self.db_session.execute(query)
        region = result.scalar()

        if region:
            await self.db_session.delete(region)
            await self.db_session.commit()
            return {"status": "success", "message": f"Регион `{region_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}

class SubregionsManager:
    """Менеджер для работы с `subregions` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_subregion(self, subregion_data: dict):
        """Добавление нового субрегиона."""
        subregion = Subregions(**subregion_data)
        self.db_session.add(subregion)
        await self.db_session.commit()
        return {"status": "success", "message": f"Субрегион `{subregion_data['name']}` создан"}

    async def get_subregion(self, subregion_id: str):
        """Получение субрегиона по ID."""
        query = select(Subregions).where(Subregions.id == subregion_id)
        result = await self.db_session.execute(query)
        subregion = result.scalar()
        return {"status": "found", "data": subregion.__dict__} if subregion else {"status": "error", "message": "Субрегион не найден"}

    async def update_subregion(self, subregion_id: str, subregion_data: dict):
        """Обновление данных субрегиона."""
        query = select(Subregions).where(Subregions.id == subregion_id)
        result = await self.db_session.execute(query)
        subregion = result.scalar()

        if subregion:
            for key, value in subregion_data.items():
                setattr(subregion, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Субрегион `{subregion_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_subregion(self, subregion_id: str):
        """Удаление субрегиона."""
        query = select(Subregions).where(Subregions.id == subregion_id)
        result = await self.db_session.execute(query)
        subregion = result.scalar()

        if subregion:
            await self.db_session.delete(subregion)
            await self.db_session.commit()
            return {"status": "success", "message": f"Субрегион `{subregion_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}