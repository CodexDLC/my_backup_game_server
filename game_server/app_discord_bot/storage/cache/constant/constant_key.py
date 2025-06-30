class RedisKeys:
    """
    Определяет шаблоны ключей и полей Redis, используемые в приложении.
    """

    # --- Глобальные ключи ---
    PENDING_REQUEST = "pending_request:{command_id}"
    PENDING_REQUEST_CONTEXT = "pending_request_context:{correlation_id}"
    AUTH_TOKEN = "auth_token:{user_id}"

    # --- Раздел 1: Конфигурация Шарда ---
    # Основной ключ-контейнер для конфигурации (тип: Hash)
    # --- Раздел 1: Конфигурация Шарда (Мастер: Discord-Бот) ---
    GUILD_CONFIG_HASH = "shard:{guild_id}:guild_config"

    # -- Поля внутри GUILD_CONFIG_HASH --
    FIELD_LAYOUT_CONFIG = "layout_config"
    FIELD_SYSTEM_ROLES = "system_roles"
    FIELD_PLAYER_DISCORD_META = "player:{account_id}:discord_meta"
    
    # НОВОЕ: Поле для хранения конфигурации Hub Layout
    FIELD_HUB_LAYOUT_CONFIG = "hub_layout_config"
    
    # --- Раздел 2: Сессии Онлайн Игроков (Мастер: Бэкенд) ---
    PLAYER_SESSION_HASH = "shard:{guild_id}:sessions" 
    # и/или другие детализированные ключи, например:
    # PLAYER_SESSION_STATUS = "shard:{guild_id}:session:{account_id}:status"
   
    # --- Раздел 3: Глобальный Индекс Состояния (Мастер: Бэкенд) ---
    GLOBAL_ONLINE_PLAYERS_HASH = "global:online_players"
