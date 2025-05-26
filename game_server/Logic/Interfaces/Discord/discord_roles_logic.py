from sqlalchemy.ext.asyncio import AsyncSession
from game_server.Logic.CRUD_LOGIC.CRUD.discord_api_route.crud_discord import manage_state_entities_discord
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.services.logging.logging_setup import logger


class StateEntitiesLogic:
    """Класс для управления ролями Discord-гильдий."""

    @staticmethod
    async def create_roles(guild_id: int, entity_data: dict) -> dict:
        """Создание ролей для указанной гильдии."""
        db_session = await get_db_session()
        return await manage_state_entities_discord("insert", guild_id, entity_data, db_session)

    @staticmethod
    async def list_roles(guild_id: int) -> list:
        """Получение всех ролей для гильдии."""
        db_session = await get_db_session()
        return await manage_state_entities_discord("get", guild_id, db_session=db_session)

    @staticmethod
    async def update_role(guild_id: int, entity_data: dict) -> dict:
        """Обновление роли по `guild_id`."""
        db_session = await get_db_session()
        return await manage_state_entities_discord("update", guild_id, entity_data, db_session)

    @staticmethod
    async def delete_role(guild_id: int) -> dict:
        """Удаление роли по `guild_id`."""
        db_session = await get_db_session()
        return await manage_state_entities_discord("delete", guild_id, db_session=db_session)
