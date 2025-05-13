from fastapi import APIRouter, HTTPException
from game_server.services.logging_config import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from game_server.database.models.models import Regions, Worlds, Subregions  # Импортируем SQLAlchemy модели


# -------------------- Модели --------------------
class WorldsResponse(BaseModel):
    id: str
    name: str
    is_static: bool
    created_at: str


# -------------------- Роуты --------------------
router = APIRouter()

@router.get("/world", response_model=WorldsResponse, summary="Получить текущий мир")
async def get_current_world():
    logger.info("Запрос на получение текущего мира")
    
    try:
        # Получаем сессию из AsyncSession
        async with get_db_session() as session:
            query = select(Worlds).order_by(Worlds.created_at.desc()).limit(1)
            result = await session.execute(query)
            world = result.scalar_one_or_none()  # Получаем первую строку, или None, если нет данных
            
            if not world:
                raise HTTPException(status_code=404, detail="Мир не найден")
            
            return WorldsResponse(**world.__dict__)  # Преобразуем в pydantic модель
            
    except Exception as e:
        logger.error(f"Ошибка при получении текущего мира: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении текущего мира")


@router.get("/regions", response_model=List[str], summary="Получить все регионы для категории в Discord")
async def get_all_regions():
    logger.info("Запрос на получение всех регионов")
    
    try:
        async with get_db_session() as session:
            query = select(Regions.region_name)  # Используем модель Regions для запроса
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail="Регионы не найдены")
            
            return [row['region_name'] for row in rows]  # Возвращаем список регионов
            
    except Exception as e:
        logger.error(f"Ошибка при получении регионов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении регионов")


@router.get("/subregions/{region_access_key}", response_model=List[str], summary="Получить подрегионы для указанного региона")
async def get_subregions(region_access_key: str):
    logger.info(f"Запрос на получение подрегионов для region_access_key={region_access_key}")
    
    try:
        async with get_db_session() as session:
            query = select(Subregions.subregion_name).where(Subregions.region_access_key == region_access_key)
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail="Подрегионы не найдены")
            
            return [row['subregion_name'] for row in rows]  # Возвращаем список подрегионов
            
    except Exception as e:
        logger.error(f"Ошибка при получении подрегионов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении подрегионов")
