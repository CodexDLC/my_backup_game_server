from sqlalchemy.ext.asyncio import AsyncSession
from game_server.Logic.CRUD_LOGIC.manager.discord_api_route.ORM_discord import AppliedPermissionsManager
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.services.logging.logging_setup import logger


class DiscordPermissionsLogic:
    """Класс логики работы с правами доступа Discord."""

    @staticmethod
    async def get_applied_permissions(guild_id: int) -> list:
        """Получение всех примененных прав для указанной гильдии."""
        async with get_db_session() as db_session:
            manager = AppliedPermissionsManager(db_session)
            return await manager.get_permissions(guild_id)

    @staticmethod
    async def apply_permissions(guild_id: int, payload: dict) -> dict:
        """Регистрация факта применения прав."""
        async with get_db_session() as db_session:
            manager = AppliedPermissionsManager(db_session)
            return await manager.create_permission(guild_id, payload)

    @staticmethod
    async def check_applied_permissions(entity_access_key: str, access_code: int, guild_id: int) -> list:
        """Проверка, были ли применены права."""
        async with get_db_session() as db_session:
            manager = AppliedPermissionsManager(db_session)
            return await manager.get_permissions(guild_id)

    @staticmethod
    async def delete_applied_permissions(guild_id: int) -> dict:
        """Удаление прав доступа."""
        async with get_db_session() as db_session:
            manager = AppliedPermissionsManager(db_session)
            return await manager.delete_permission(guild_id)
