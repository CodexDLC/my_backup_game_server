from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.Logic.Interfaces.Discord.discord_permissions_logic import (
    DiscordPermissionsLogic
)
from game_server.services.logging.logging_setup import logger

class DiscordPermissionsRoutes:
    """Класс маршрутов для управления правами Discord."""

    def __init__(self):
        self.router = APIRouter()
        self.router.get("/applied-permissions")(self.get_applied_permissions_route)
        self.router.post("/applied-permissions")(self.apply_permissions_route)
        self.router.get("/applied-permissions/{entity_access_key}/{access_code}")(self.check_applied_permissions_route)
        self.router.delete("/applied-permissions/{entity_access_key}/{access_code}/{target_type}/{target_id}/{role_id}")(self.delete_applied_permissions_route)
        self.router.get("/permissions/{entity_access_key}")(self.get_permissions_route)

    async def get_applied_permissions_route(
        self, guild_id: int, db_session: AsyncSession = Depends(get_db_session)
    ):
        logger.info(f"Запрос на получение примененных прав для guild_id={guild_id}")
        return await DiscordPermissionsLogic.get_applied_permissions(guild_id)

    async def apply_permissions_route(
        self, guild_id: int, payload: dict, db_session: AsyncSession = Depends(get_db_session)
    ):
        logger.info(f"Регистрация прав для guild_id={guild_id}, entity_access_key={payload['entity_access_key']}")
        return await DiscordPermissionsLogic.apply_permissions(guild_id, payload)

    async def check_applied_permissions_route(
        self, entity_access_key: str, access_code: int, guild_id: int, db_session: AsyncSession = Depends(get_db_session)
    ):
        logger.info(f"Проверка прав для entity_access_key={entity_access_key}, access_code={access_code}, guild_id={guild_id}")
        return await DiscordPermissionsLogic.check_applied_permissions(entity_access_key, access_code, guild_id)

    async def delete_applied_permissions_route(
        self, entity_access_key: str, access_code: int, target_type: str, target_id: int, role_id: int, guild_id: int,
        db_session: AsyncSession = Depends(get_db_session)
    ):
        logger.info(f"Удаление записи прав для entity_access_key={entity_access_key}")
        try:
            return await DiscordPermissionsLogic.delete_applied_permissions(entity_access_key, access_code, target_type, target_id, role_id, guild_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Запись не найдена")

    async def get_permissions_route(
        self, entity_access_key: str, db_session: AsyncSession = Depends(get_db_session)
    ):
        logger.info(f"🔐 Запрос прав доступа для entity_access_key={entity_access_key}")
        return await DiscordPermissionsLogic.get_permissions(entity_access_key)

# 📌 Создаём экземпляр маршрутов
discord_permissions_routes = DiscordPermissionsRoutes().router
