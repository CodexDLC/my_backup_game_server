# Импортируем роутеры для Discord
from game_server.api.routers.discord.discord_roles import router as discord_roles_router
from game_server.api.routers.discord.discord_permissions import router as discord_permissions_router
from game_server.api.routers.discord.discord_bindings import router as discord_bindings_router

# Если нужно указать доступные модули для импорта:
__all__ = [
    "discord_roles_router",
    "discord_permissions_router",
    "discord_bindings_router"
]


