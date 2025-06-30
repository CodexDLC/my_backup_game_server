# game_server/config/constants/redis/discord_keys.py

# === КЛЮЧИ ДЛЯ ДАННЫХ, СИНХРОНИЗИРОВАННЫХ С DISCORD-БОТОМ ===

# Ключ-контейнер для конфигурации шарда (тип: Hash)
# Обратите внимание на префикс "discord:", который мы обсуждали
KEY_GUILD_CONFIG_HASH = "discord:shard:{guild_id}:guild_config"

# Имена полей внутри этого Hash'а. Они должны совпадать с теми, что на стороне бота.
FIELD_LAYOUT_CONFIG = "layout_config"
FIELD_SYSTEM_ROLES = "system_roles"
FIELD_PLAYER_DISCORD_META = "player:{account_id}:discord_meta"