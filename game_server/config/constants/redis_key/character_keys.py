# game_server/config/constants/redis/character_keys.py

# === КЛЮЧИ, СВЯЗАННЫЕ С ПЕРСОНАЖАМИ ===

# Шаблон для ключа-контейнера данных персонажа (тип: Hash)
# Требует и account_id, и character_id
KEY_CHARACTER_DATA = "world:account:{account_id}:character:{character_id}"

# Имя поля внутри Hash'а персонажа, где будет лежать полный слепок данных
FIELD_CHARACTER_SNAPSHOT = "snapshot"


# === КЛЮЧИ, СВЯЗАННЫЕ С ГЛОБАЛЬНОЙ СТАТИСТИКОЙ ===

# Ключ для Hash'а с глобальной статистикой мира
KEY_WORLD_STATS = "world:stats"

# Имя поля внутри Hash'а статистики для счетчика доступных персонажей
FIELD_CHARACTER_POOL_AVAILABLE = "character_pool_available"