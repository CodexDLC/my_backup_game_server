from fastapi import APIRouter, HTTPException
from game_server.Logic.Interfaces.Discord.discord_roles_logic import StateEntitiesLogic
from game_server.services.logging.logging_setup import logger

class DiscordRolesRoutes:
    """Класс маршрутов для управления ролями Discord-гильдий."""

    def __init__(self):
        self.router = APIRouter()
        self.router.post("/create_roles")(self.create_roles_route)
        self.router.get("/list_roles/{guild_id}")(self.list_roles_route)
        self.router.delete("/delete_role/{guild_id}/{access_code}")(self.delete_role_route)
        self.router.delete("/delete_all_roles/{guild_id}")(self.delete_all_roles_route)

    async def create_roles_route(self, payload: dict):
        """Создание ролей."""
        logger.info(f"Создание ролей для guild_id={payload['guild_id']}")
        return await StateEntitiesLogic.create_roles(payload["guild_id"], payload)

    async def list_roles_route(self, guild_id: int):
        """Получение списка ролей."""
        logger.info(f"Запрос ролей для guild_id={guild_id}")
        return await StateEntitiesLogic.list_roles(guild_id)

    async def delete_role_route(self, guild_id: int, access_code: int):
        """Удаление одной роли."""
        logger.info(f"Удаление роли для guild_id={guild_id}, access_code={access_code}")
        try:
            return await StateEntitiesLogic.delete_role(guild_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Роль не найдена")

    async def delete_all_roles_route(self, guild_id: int):
        """Удаление всех ролей."""
        logger.info(f"Удаление всех ролей для guild_id={guild_id}")
        try:
            return await StateEntitiesLogic.delete_role(guild_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Роли не найдены")

# 📌 Создаём экземпляр класса с роутами
discord_roles_routes = DiscordRolesRoutes().router
