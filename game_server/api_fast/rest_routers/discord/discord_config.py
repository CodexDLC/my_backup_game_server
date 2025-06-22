# rest_routers/discord/discord_config.py

from game_server.api_fast.rest_routers.discord.discord_entity import discord_entity_router
from game_server.api_fast.rest_routers.discord.discord_roles_mapping import discord_roles_mapping_router 


discord_routers = [
    # --- НОВАЯ КОНФИГУРАЦИЯ ДЛЯ DISCORDENTITY РОУТОВ ---
    {
        "router": discord_entity_router,
        "prefix": "/discord-entities", # Этот префикс мы обсуждали ранее
        "tags": ["Discord"], # Более конкретный тег
        "description": "API endpoints for managing Discord channels and categories (DiscordEntity table)."
    },
    # --- НОВАЯ КОНФИГУРАЦИЯ ДЛЯ DISCORD_ROLES_MAPPING РОУТОВ ---
    {
        "router": discord_roles_mapping_router,
        "prefix": "/discord-roles-mapping",
        "tags": ["Discord"],
        "description": "API endpoints for managing Discord roles mapping (StateEntityDiscord table)."
    }
]


