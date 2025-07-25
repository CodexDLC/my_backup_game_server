# game_server/app_discord_bot/config/event_to_custom_id_config.py

"""
Реестр для преобразования серверных событий в custom_id для InteractionRouter.
"""

EVENT_TO_CUSTOM_ID_MAP = {
    "event.location.updated": {
        # Шаблон для custom_id. В {} подставляются ключи из данных события.
        "custom_id_format": "cache:update_location:{location_id}",
    },

}