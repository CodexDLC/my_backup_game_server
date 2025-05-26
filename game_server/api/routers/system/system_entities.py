# game_server/api/routers/system/system_entities.py

from typing import List
from fastapi import APIRouter, HTTPException


from game_server.services.logging.logging_setup import logger


router = APIRouter()

@router.get("/available", response_model=List[str], summary="Получить доступные флаги для сущностей")
async def get_available_flags_route():
    logger.info("Запрос на получение доступных флагов для сущностей")
    try:
        return await get_available_flags()
    except ValueError:
        raise HTTPException(status_code=404, detail="Флаги не найдены")
