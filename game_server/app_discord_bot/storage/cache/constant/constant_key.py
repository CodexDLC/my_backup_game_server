class RedisKeys:
    """
    Определяет шаблоны ключей и полей Redis, используемые в приложении.
    Структура организована по функциональным доменам.
    """

    # ===================================================================
    # 🏦 ГЛОБАЛЬНЫЕ КЛЮЧИ (не привязаны к гильдиям)
    # ===================================================================
    # Используются для асинхронных запросов и межсервисного взаимодействия.
    PENDING_REQUEST_CONTEXT = "pending_request_context:{correlation_id}"
    AUTH_TOKEN = "auth_token:{user_id}"

    # Используется бэкендом для быстрого поиска account_id по discord_id
    GLOBAL_BACKEND_DISCORD_TO_ACCOUNT_MAPPING = "global:backend:discord_to_game_account:{discord_user_id}"
    
    # 🔥 НОВОЕ: Глобальное множество ID всех онлайн персонажей
    GLOBAL_ONLINE_PLAYERS_SET = "global:online_players"


    # ===================================================================
    # ⚙️ КОНФИГУРАЦИЯ ГИЛЬДИИ/ШАРДА (Мастер: Discord-Бот)
    # ===================================================================
    # Хэш, содержащий все настройки для конкретной гильдии (Хаба или Игрового шарда).
    GUILD_CONFIG_HASH = "shard:{shard_type}:{guild_id}:config"

    # --- Поля внутри GUILD_CONFIG_HASH ---
    FIELD_LAYOUT_CONFIG = "layout_config"
    FIELD_SYSTEM_ROLES = "system_roles"
    FIELD_REGISTRATION_MESSAGE_ID = "registration_message_id"
    FIELD_LOGIN_MESSAGE_ID = "login_message_id"
    FIELD_REGISTERED_PLAYER_IDS = "registered_player_ids"


    # ===================================================================
    # 👤 ДАННЫЕ АККАУНТА ИГРОКА НА ШАРДЕ (Мастер: Discord-Бот)
    # ===================================================================
    # Основной хэш, содержащий все данные игрока, специфичные для данного шарда.
    PLAYER_ACCOUNT_DATA_HASH = "shard:game:{shard_id}:account_by_discord:{discord_user_id}"

    # --- Поля внутри PLAYER_ACCOUNT_DATA_HASH ---
    FIELD_ACCOUNT_ID = "account_id"
    FIELD_GENERAL_INFO = "general_info"
    FIELD_LINKED_DISCORD_META = "linked_discord_meta"
    FIELD_DISCORD_ROLES = "discord_roles"
    FIELD_DISCORD_CHANNELS = "discord_channels"
    FIELD_MESSAGES = "messages"
    # 🔥 НОВОЕ: Поле для хранения списка ID персонажей на аккаунте
    FIELD_CHARACTER_IDS = "character_ids"


    # ===================================================================
    # 🎮 ИГРОВЫЕ СЕССИИ (Мастер: Discord-Бот)
    # ===================================================================
    # 🔥 НОВОЕ: Ключ для хранения детальных данных сессии персонажа (теплый кэш)
    CHARACTER_SESSION_HASH = "shard:game:{guild_id}:online_session:{character_id}"

    # Хэш, содержащий ключевые ID активной сессии пользователя.
    ACTIVE_USER_SESSION_HASH = "active_session:by_discord:{discord_id}"

    # --- Поля внутри ACTIVE_USER_SESSION_HASH ---
    FIELD_SESSION_ACCOUNT_ID = "account_id"
    FIELD_SESSION_CHARACTER_ID = "character_id"


    # --- Поля внутри CHARACTER_SESSION_HASH (обновлено на основе скриншота) ---
    FIELD_SESSION_CORE = "core"
    FIELD_SESSION_QUESTS = "quests"
    FIELD_SESSION_REPUTATION = "reputation"
    FIELD_SESSION_SKILLS = "skills"
    FIELD_SESSION_VITALS = "vitals"
    FIELD_SESSION_STATS = "stats"
    FIELD_SESSION_SESSION = "session" # Переименовано, чтобы избежать конфликта с именем ключа
    FIELD_SESSION_ITEMS = "items"
    FIELD_SESSION_LOCATION = "location"
    FIELD_SESSION_ABILITIES = "abilities"
    FIELD_SESSION_DERIVED_STATS = "derived_stats"


    # ===================================================================
    # 🗺️ Карта мира (Пример, если будет кэшироваться)
    # =================================================================== 
    
    GLOBAL_GAME_WORLD_DATA = "global:game_world_data"
    
    GLOBAL_GAME_WORLD_DYNAMIC_LOCATION_DATA = "global:game_world_data_dynamic:{location_id}" # <--- ДОБАВЛЕНО

    # --- Поля внутри GLOBAL_GAME_WORLD_DYNAMIC_LOCATION_DATA (пример) ---
    FIELD_DYNAMIC_PLAYERS_COUNT = "players_in_location" # Пример поля
    FIELD_DYNAMIC_NPCS_COUNT = "npcs_in_location"       # Пример поля
    FIELD_DYNAMIC_LAST_UPDATE = "last_update"           # Пример поля