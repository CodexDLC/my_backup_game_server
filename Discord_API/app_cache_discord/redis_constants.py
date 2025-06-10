# Discord_API\app_cache\redis_constants.py

# Константы для префиксов ключей в локальном Redis Discord-бота
# Эти префиксы используются для построения "папок" в структуре ключей Redis
KEY_PREFIX_USERS = "discord_bot_cache:users"
KEY_PREFIX_CHANNELS_CONTEXT = "discord_bot_cache:users:{discord_account_id}:channel_context"
KEY_PREFIX_DISPLAYED_ITEMS = "discord_bot_cache:users:{discord_account_id}:displayed_items"
KEY_PREFIX_REF_DATA = "discord_bot_cache:ref_data"

# Константы для отдельных "файлов" в пользовательских "папках"
KEY_FILE_USER_PROFILE = "profile"
KEY_FILE_USER_STATUS_FLAGS = "status_flags"
KEY_FILE_USER_CHARACTER_SNAPSHOT = "character_snapshot"
KEY_FILE_USER_INVENTORY_SNAPSHOT = "inventory_snapshot"
KEY_FILE_USER_GROUP_SNAPSHOT = "group_snapshot"
KEY_FILE_USER_CHANNEL_IDS_LIST = "channel_ids"


# Константы для TTL (Time To Live) в секундах для локального Redis бота
# Эти значения будут импортированы из game_server.config.settings.py,
# но здесь мы определяем их как заглушки/документацию
# Их реальные значения будут браться из environment variables через settings.py
DEFAULT_TTL_USER_CONTEXT = 3600             # 1 час: для основного контекста пользователя (профиль, снапшоты)
DEFAULT_TTL_CHANNEL_CONTEXT = 1200          # 20 минут: для контекста конкретного канала
DEFAULT_TTL_DISPLAYED_ITEM = 600            # 10 минут: для контекста отображаемых предметов
DEFAULT_TTL_REF_DATA = 0                    # 0 = бессрочно: для глобальных справочных данных


# Добавьте эти константы в game_server/config/settings.py, если их там нет.
# Например:
# from .redis_constants import (
#     KEY_PREFIX_USERS, # и т.д.
#     DEFAULT_TTL_USER_CONTEXT # и т.д.
# )