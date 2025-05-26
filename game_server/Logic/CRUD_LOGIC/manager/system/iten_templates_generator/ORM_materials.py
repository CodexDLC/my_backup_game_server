

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import Materials

class MaterialsManager:
    """Менеджер для работы с `materials` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_material(self, material_id: int, material_data: dict):
        """Добавление нового материала."""
        material = Materials(id=material_id, **material_data)
        self.db_session.add(material)
        await self.db_session.commit()
        return {"status": "success", "message": f"Материал `{material_data['name']}` добавлен"}

    async def get_material(self, material_id: int):
        """Получение материала по его ID."""
        query = select(Materials).where(Materials.id == material_id)
        result = await self.db_session.execute(query)
        material = result.scalar()
        return {"status": "found", "data": material.__dict__} if material else {"status": "error", "message": "Материал не найден"}

    async def update_material(self, material_id: int, material_data: dict):
        """Обновление данных материала."""
        query = select(Materials).where(Materials.id == material_id)
        result = await self.db_session.execute(query)
        material = result.scalar()

        if material:
            for key, value in material_data.items():
                setattr(material, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Материал `{material_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_material(self, material_id: int):
        """Удаление материала."""
        query = select(Materials).where(Materials.id == material_id)
        result = await self.db_session.execute(query)
        material = result.scalar()

        if material:
            await self.db_session.delete(material)
            await self.db_session.commit()
            return {"status": "success", "message": f"Материал `{material_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
