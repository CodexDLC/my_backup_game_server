# game_server/app_discord_bot/app/configs/entity_actions_config.py

"""
Центральный конфигурационный файл для определения динамических кнопок действий
для различных типов и состояний сущностей.
"""

# Кнопки для подтипов НЕЙТРАЛЬНЫХ NPC
# Ключ - это подтип NPC (например, из поля 'type' или 'subtype' в данных сущности)
NPC_NEUTRAL_SUBTYPE_ACTIONS = {
    "Торговец": [
        {
            "key": "trade", 
            "label": "Торговать", 
            "style": "green",
            "custom_id_template": "trade:initiate:{entity_id}"
        }
    ],
    "quest_giver": [
        {
            "key": "quest", 
            "label": "Задание", 
            "style": "success",
            "custom_id_template": "quest:start:{entity_id}"
        }
    ]
}

# Кнопки для ВРАЖДЕБНЫХ NPC (бывшие монстры)
NPC_ENEMY_ACTIONS = {
    # Для врагов пока одно действие - атаковать. 
    # Ключ "default" используется, если у врагов нет разных подтипов.
    "default": [
        {
            "key": "attack",
            "label": "Атаковать",
            "style": "danger",
            "custom_id_template": "combat:attack:{entity_id}"
        }
    ]
}


# Кнопки для состояний сундуков
CHEST_STATE_ACTIONS = {
    "Закрыт": [
        {
            "key": "unlock", 
            "label": "Взломать", 
            "style": "secondary",
            "custom_id_template": "chest:unlock:{entity_id}"
        }
    ]
}