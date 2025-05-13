
from game_server.api.routers.system.system_mapping import router as system_mapping_router
from game_server.api.routers.system.system_gameworld import router as system_gameworld_router
from game_server.api.routers.system.system_entities import router as system_entities_router

# Если нужно указать доступные модули для импорта:
__all__ = [
    "system_mapping_router",
    "system_gameworld_router",
    "system_entities_router"
]