from game_server.api_rest.routers.system import (
    system_accaunt_router,
    system_gameworld_router,
    system_mapping_route,
)
from .routers.discord import (
    discord_bindings_router,
    state_entities_discord_router
)
from .routers.character import (
    auto_session_router,

)

from game_server.api_rest.routers.utils_route import import_yami_route
from game_server.api_rest.routers import random_pool_router, health_router # health_router теперь импортирован

from game_server.api_rest.routers.test.test_generators import test_generators_router

ROUTERS_CONFIG = [

    # System routers
    {
        "router": system_gameworld_router,
        "prefix": "/system/gameworld",
        "tags": ["System"],
        "description": "Операции с игровым миром"
    },
    {
        "router": system_accaunt_router,
        "prefix": "/system/account",
        "tags": ["System"],
        "description": "Управление учетными записями"
    },
    {
        "router": system_mapping_route,
        "prefix": "/system/mapping",
        "tags": ["System"],
        "description": "Управление картами и локациями"
    },
    
    # Random pool routers
    {
        "router": random_pool_router,
        "prefix": "/random",
        "tags": ["Random"],
        "description": "Генерация случайных значений"
    }, # 🔥 Убрал лишнюю запятую перед следующим элементом, если это был конец списка
    
    # Character routers
    {
        "router": auto_session_router,
        "prefix": "/character/auto_session",
        "tags": ["Character"],
        "description": "Автоматическая сессия персонажа"
    },
    
    # Utils routes
    {
        "router": import_yami_route,
        "prefix": "/export",
        "tags": ["utils_route"],
        "description": "Утилиты"
    },
    
    # Discord routers
    {
        "router": discord_bindings_router,
        "prefix": "/discord/bindings",
        "tags": ["Discord"],
        "description": "Роуты для управления связями"
    },

    {
        "router": state_entities_discord_router,
        "prefix": "/discord", # Будьте внимательны: если другие роуты Discord также используют "/discord" без подпрефикса, могут быть конфликты путей.
        "tags": ["Discord"],
        "description": "Роуты для управления игровыми сущностями"
    },
    
    # 🔥 Health Check router - теперь он здесь
    {
        "router": health_router,
        "prefix": "", # Оставляем пустым, чтобы эндпоинт был /health
        "tags": ["Health Check"],
        "description": "Проверка состояния и работоспособности сервиса."
    },
    {
        "router": test_generators_router,
        "prefix": "", # Оставляем пустым, чтобы эндпоинт был /health
        "tags": ["test"],
        "description": "Проверка и тестовые роуты функций "
    }
]