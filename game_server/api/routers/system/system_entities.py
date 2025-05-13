from fastapi import APIRouter, HTTPException, Depends
from game_server.database.models.models import StateEntities
from game_server.services.logging_config import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session  # Подключаем сессию SQLAlchemy
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# -------------------- Модели --------------------
class FlagResponse(BaseModel):
    flag_name: str

# -------------------- Роуты --------------------
router = APIRouter()

@router.get("/available", response_model=List[str], summary="Получить доступные флаги для сущностей")
async def get_available_flags(db: AsyncSession = Depends(get_db_session)):  # Подключаем сессию SQLAlchemy
    logger.info("Запрос на получение доступных флагов для сущностей")
    
    try:
        # Запрос через SQLAlchemy
        stmt = select(StateEntities)  # Предполагаем, что EntityFlag это модель для таблицы entity_flags
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            raise HTTPException(status_code=404, detail="Флаги не найдены")
        
        return [row.flag_name for row in rows]
    
    except Exception as e:
        logger.error(f"Ошибка при получении флагов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении флагов")
