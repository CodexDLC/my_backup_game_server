# game_server/api_fast/rest_routers/routers_config.py

# --- Импортируем наши роутеры ---
from game_server.app_gateway.rest_routers.system.discord.discord_sync_routes import discord_sync_router
from game_server.app_gateway.rest_routers.system.discord.discord_delete_routes import discord_delete_router
from game_server.app_gateway.rest_routers.system.discord.discord_get_routes import discord_get_router
from game_server.app_gateway.rest_routers.system.shard.shard_routes import shard_router
from game_server.app_gateway.rest_routers.system.state_entity.state_entity_routes import state_entity_router # <-- НОВЫЙ ИМПОРТ
from game_server.app_gateway.rest_routers.system.discord.discord_config_sync_routes import discord_config_sync_routes
system_routers = [
    # --- Роутеры для Discord ---
    { "router": discord_sync_router, "prefix": "/discord", "tags": ["System :: Discord"] },
    { "router": discord_delete_router, "prefix": "/discord", "tags": ["System :: Discord"] },
    { "router": discord_get_router, "prefix": "/discord", "tags": ["System :: Discord"] },
    { "router": discord_config_sync_routes, "prefix": "/discord", "tags": ["System :: Discord"] },
    
    # --- РОУТЕРЫ ДЛЯ ШАРДОВ ---
    { "router": shard_router, "prefix": "/shards", "tags": ["System :: Shard Management"] },

    # --- НОВЫЙ РОУТЕР ДЛЯ STATE ENTITY ---
    { "router": state_entity_router, "prefix": "/state-entities", "tags": ["System :: State Entities"] },
]


