from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.DomainLogic.CharacterLogic.auto_session.autosesion import AutoSession
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session



router = APIRouter()

CategoryType = Literal["Crafting", "General", "Exploration", "Trade"]
IdentifierType = Literal["id", "name", "discord_id"]
ActionType = Literal["start", "stop", "status", "update"]

@router.post("/handle")
async def handle_session(
    action: ActionType = Query(...),
    identifier_type: IdentifierType = Query(...),
    identifier_value: str = Query(..., min_length=1),
    category: Optional[CategoryType] = Query(None),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Универсальный обработчик сессии персонажа с привязкой категории."""
    if action == "start" and not category:
        return {"status": "error", "message": "❌ Для `start` необходимо указать `category`!"}

    auto_session = AutoSession(db_session)
    result = await auto_session.handle(action, identifier_type, identifier_value, category)
    return result

auto_session_router = router