# game_server/config/constants/redis/shard_keys.py

# Шаблон для ключа-контейнера статистики шарда (тип: Hash)
KEY_SHARD_STATS = "discord:shard:{discord_guild_id}:stats"

# Имя поля внутри Hash'а для счетчика игроков
FIELD_SHARD_PLAYER_COUNT = "player_count"