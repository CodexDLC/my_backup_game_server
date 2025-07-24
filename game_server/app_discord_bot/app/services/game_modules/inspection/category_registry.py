# game_server/app_discord_bot/app/services/game_modules/inspection/category_registry.py

"""
Реестр категорий сущностей для модуля 'Осмотр'.
Определяет отображаемые имена, ключи описаний и группы для эмбедов.
"""

CATEGORY_REGISTRY = {
    "players": {
        "display_name": "Игроки",
        "description_key": "PLAYERS_IN_SHADOW",
        "embed_group": "dynamic_entities"
    },
    "npc_neutral": {
        "display_name": "Персонажи",
        "description_key": "NPCS_NEARBY",
        "embed_group": "dynamic_entities"
    },
    "npc_enemy": {
        "display_name": "Противники",
        "description_key": "MONSTERS_IN_AREA",
        "embed_group": "dynamic_entities"
    },
    "chests": {
        "display_name": "Сундуки",
        "description_key": "CHESTS_AROUND",
        "embed_group": "environmental_objects"
    },
    "battle": {
        "display_name": "Поле боя",
        "description_key": "BATTLE_FIELD",
        "embed_group": "dynamic_entities" 
    },
    "portals": {
        "display_name": "Порталы",
        "description_key": "PORTALS_AVAILABLE",
        "embed_group": "environmental_objects"
    },
    "merchants": {
        "display_name": "Торговцы",
        "description_key": "MERCHANTS_NEARBY",
        "embed_group": "dynamic_entities"
    },
    "crafting_stations": {
        "display_name": "Станции крафта",
        "description_key": "CRAFTING_STATIONS_NEARBY",
        "embed_group": "environmental_objects"
    }
}