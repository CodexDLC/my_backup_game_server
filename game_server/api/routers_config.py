from game_server.api.routers.discord import (
    discord_bindings_router,
    discord_roles_router,
    discord_permissions_router
)
from game_server.api.routers.system import (
    system_gameworld_router,
    system_entities_router,
    system_mapping_router,
    system_tick_router
)
from game_server.api.routers.character import character_sync_router
from game_server.api.routers import random_pool_route




ROUTERS_CONFIG = [
    # Discord routers
    {
        "router": discord_bindings_router,
        "prefix": "/discord/bindings",
        "tags": ["Discord"],
        "description": "Управление привязками Discord аккаунтов"
    },
    {
        "router": discord_roles_router,
        "prefix": "/discord/roles",
        "tags": ["Discord"],
        "description": "Управление ролями Discord"
    },
    {
        "router": discord_permissions_router,
        "prefix": "/discord/permissions",
        "tags": ["Discord"],
        "description": "Управление правами доступа Discord"
    },
    
    # System routers
    {
        "router": system_gameworld_router,
        "prefix": "/system/gameworld",
        "tags": ["System"],
        "description": "Операции с игровым миром"
    },
    {
        "router": system_entities_router,
        "prefix": "/system/entities",
        "tags": ["System"],
        "description": "Управление игровыми сущностями"
    },
    {
        "router": system_mapping_router,
        "prefix": "/system/mapping",
        "tags": ["System"],
        "description": "Работа с картами игрового мира"
    },
    {
        "router": system_tick_router,
        "prefix": "/system/tick",
        "tags": ["System"],
        "description": "Тик игрового времени"
    },
    
    # Character routers
    {
        "router": character_sync_router,
        "prefix": "/character",
        "tags": ["Character"],
        "description": "Синхронизация данных персонажей"
    },
    
    # Random pool routers
    {
        "router": random_pool_route,
        "prefix": "/random",
        "tags": ["Random"],
        "description": "Генерация случайных значений"
    }
]


