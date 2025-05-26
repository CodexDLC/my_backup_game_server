# game_server/api/routers/system/system_tick.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


from game_server.services.logging.logging_setup import logger




router = APIRouter()
class AutoSessionRequest(BaseModel):
    character_id: int  # ✅ Одно значение вместо списка
    category: str
    
@router.post("/auto-session/start", summary="Запуск авто-сессии")
async def start_auto_session_route(payload: AutoSessionRequest):
    if payload.category not in ["exploration", "crafting", "trade", "general"]:
        raise HTTPException(status_code=400, detail="❌ Неверная категория!")
    
    logger.info(f"🚀 Запуск авто-сессии для персонажа {payload.character_id}, категория {payload.category}")
    
    try:
        return await start_auto_session(payload.character_id, payload.category)
    except ValueError:
        raise HTTPException(status_code=404, detail="❌ Персонаж не найден")

@router.delete("/auto-session/delete", summary="Удаление авто-сессии")
async def delete_auto_session_route(player_id: int):
    logger.info(f"🗑️ Удаление авто-сессии для персонажа {player_id}")
    return await delete_auto_session(player_id)

@router.get("/auto-session/status", summary="Получение статуса авто-сессии")
async def get_auto_session_status_route(player_id: int):
    logger.info(f"🔎 Запрос статуса авто-сессии для персонажа {player_id}")
    return await get_auto_session_status(player_id)

