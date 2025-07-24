# game_server\config\constants\redis_key\location_dinamic.py

"""
Единый источник правды для всех ключей и имён полей, используемых в Redis.
"""

# ===================================================================
# 🧱 Префиксы (Namespaces)
# Позволяют избежать конфликтов, если Redis используется для разных систем.
# ===================================================================
GAME_PREFIX = "game"


# ===================================================================
# 🗺️ Состояние игрового мира
# ===================================================================

# --- ШАБЛОНЫ КЛЮЧЕЙ ---

# Хэш, содержащий сводные (агрегированные) данные по конкретной локации.
# Используется для быстрого отображения команды "Осмотреться".
# Пример: game:world:location_summary:201
LOCATION_SUMMARY_HASH = f"{GAME_PREFIX}:world:location_summary:{{location_id}}"

# --- ПОЛЯ ВНУТРИ ХЭША LOCATION_SUMMARY_HASH ---

# Эти имена полей будут использоваться как в Redis, так и в коде Дискорд-бота.
# Это и есть наш "контракт" между бэкендом и клиентами.

FIELD_PLAYERS_COUNT = "players"
FIELD_NEUTRAL_NPCS_COUNT = "npc_neutral"
FIELD_ENEMY_NPCS_COUNT = "npc_enemy"
FIELD_BATTLES_COUNT = "battle"
FIELD_MERCHANTS_COUNT = "merchants"
FIELD_CHESTS_COUNT = "chests"
FIELD_PORTALS_COUNT = "portals"
FIELD_CRAFTING_STATIONS_COUNT = "crafting_stations"
FIELD_LAST_UPDATE = "last_update"


