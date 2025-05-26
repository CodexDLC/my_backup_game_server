from sqlalchemy.ext.asyncio import AsyncSession
from game_server.Logic.CRUD_LOGIC.manager.discord_api_route.ORM_discord import DiscordBindingsManager
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.services.logging.logging_setup import logger


class DiscordBindingLogic:
    """Класс для управления привязками Discord-гильдий."""

    @staticmethod
    async def save_binding(guild_id: int, entity_access_key: str, payload: dict) -> dict:
        """Сохранение или обновление привязки Discord."""
        async with get_db_session() as db_session:
            manager = DiscordBindingsManager(db_session)
            return await manager.create_binding(guild_id, payload)

    @staticmethod
    async def get_bindings(guild_id: int) -> list:
        """Получение всех привязок для гильдии."""
        async with get_db_session() as db_session:
            manager = DiscordBindingsManager(db_session)
            return await manager.get_binding(guild_id)

    @staticmethod
    async def update_binding(guild_id: int, payload: dict) -> dict:
        """Обновление привязки Discord."""
        async with get_db_session() as db_session:
            manager = DiscordBindingsManager(db_session)
            return await manager.update_binding(guild_id, payload)

    @staticmethod
    async def delete_binding(guild_id: int) -> dict:
        """Удаление привязки Discord."""
        async with get_db_session() as db_session:
            manager = DiscordBindingsManager(db_session)
            return await manager.delete_binding(guild_id)
