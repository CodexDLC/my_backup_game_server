from datetime import datetime
import uuid
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from game_server.database.models.models import Regions, Subregions, Worlds



class WorldSchema(BaseModel):
    world_id: uuid.UUID
    world_name: str
    is_static: bool
    created_at: datetime

    class Config:
        from_attributes = True  # ✅ Теперь схема поддерживает ORM-объекты
        arbitrary_types_allowed = True # <-- ВОТ ЭТА СТРОКА РЕШАЕТ ПРОБЛЕМУ С DATETIME!
        
class SystemGameWorldLogic:
    """Класс для управления игровым миром, регионами и подрегионами с использованием ORM."""

    @staticmethod
    async def get_current_world(db_session: AsyncSession):
        """Получить все данные текущего игрового мира (ORM)"""
        result = await db_session.execute(select(Worlds).limit(1))
        row = result.scalars().first()
        
        return {"status": "found", "data": WorldSchema.model_validate(row).model_dump()} if row else {"status": "error", "message": "Мир не найден"}


    @staticmethod
    async def get_all_regions(db_session: AsyncSession):
        """Получить список всех регионов (ORM)"""
        result = await db_session.execute(select(Regions))
        rows = result.scalars().all()
        
        return {"status": "found", "data": [row.to_dict() for row in rows]} if rows else {"status": "error", "message": "Регионы не найдены"}

    @staticmethod
    async def get_all_subregions(db_session: AsyncSession):
        """Получить все подрегионы без фильтрации (ORM)"""
        result = await db_session.execute(select(Subregions))
        rows = result.scalars().all()
        return {"status": "found", "data": [row.to_dict() for row in rows]} if rows else {"status": "error", "message": "Подрегионы не найдены"}


    @staticmethod
    def handle_response(result, error_message):
        """Обрабатывает ответ CRUD-функций и возвращает ВСЕ данные."""
        if not result or "status" not in result:
            raise HTTPException(status_code=500, detail="Ошибка обработки ответа")

        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=error_message)

        return result.get("data", [])  # Возвращаем весь список без фильтрации по ключу
