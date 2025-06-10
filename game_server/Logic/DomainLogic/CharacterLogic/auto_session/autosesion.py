from datetime import datetime, timedelta
from typing import Literal, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession


from game_server.Logic.DomainLogic.dom_utils.account_identifiers import AccountIdentifiers
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.system.manager_tick_handler.ORM_Auto_Sessions import AutoSessionsManager

ActionType = Literal["start", "stop", "status", "update"]
IdentifierType = Literal["id", "name", "discord_id"]

class AutoSession:
    """Лёгкая обёртка над AutoSessionsManager."""
    
    def __init__(self, db_session: AsyncSession):
        self.manager = AutoSessionsManager(db_session)
        self.identifiers = AccountIdentifiers(db_session)

    async def handle(
        self,
        action: ActionType,
        identifier_type: IdentifierType,
        identifier_value: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Только маршрутизация вызовов к менеджеру."""
        if not (character_id := await self.identifiers.get_character_id(identifier_type, identifier_value)):
            return {"status": "error", "message": "Персонаж не найден!"}

        try:
            match action:
                case "start" if category:
                    return await self._start(character_id, category)
                case "stop":
                    return await self.manager.delete_session(character_id)
                case "status":
                    return await self.manager.get_session(character_id)
                case "update":
                    return await self._update(character_id)
                case _:
                    return {"status": "error", "message": "Неверная команда!"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка: {e}"}

    async def _start(self, character_id: int, category: str) -> Dict[str, Any]:
        """Сокращённый вызов менеджера для старта сессии."""
        return await self.manager.create_session(
            character_id=character_id,
            active_category=category,
            next_tick_at=datetime.utcnow() + timedelta(minutes=6),
            last_tick_at=datetime.utcnow()
        )

    async def _update(self, character_id: int) -> Dict[str, Any]:
        """Сокращённый вызов для обновления."""
        return await self.manager.update_session(
            character_id,
            {"next_tick_at": datetime.utcnow() + timedelta(minutes=6)}
        )