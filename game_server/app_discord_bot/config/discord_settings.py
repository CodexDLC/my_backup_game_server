# Discord_API\discord_settings.py

import os
from dotenv import load_dotenv

load_dotenv()

# --- Настройки для API и серверных параметров ---
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

PUBLIC_GAME_SERVER_API = os.getenv("PUBLIC_GAME_SERVER_API")
INTERNAL_GAME_SERVER_API = os.getenv("INTERNAL_GAME_SERVER_API")

# Основной URL для взаимодействия с игровым сервером/бэкендом
GAME_SERVER_API = os.getenv("GAME_SERVER_API")
if not GAME_SERVER_API:
    raise ValueError("❌ Ошибка: переменная окружения GAME_SERVER_API не задана!")

# API_URL для Discord-бота теперь явно ссылается на GAME_SERVER_API
API_URL = GAME_SERVER_API

RANDOM_API_URL = os.getenv("RANDOM_API_URL")

# --- ИЗМЕНЕНИЕ ЗДЕСЬ: GATEWAY_URL берется из GAME_SERVER_API ---
GATEWAY_URL = os.getenv("GAME_SERVER_API_WEBSOCKET") # Теперь GATEWAY_URL будет использовать новый полный URL
# -------------------------------------------------------------

GATEWAY_AUTH_TOKEN = os.getenv("GATEWAY_BOT_SECRET")
if not GATEWAY_AUTH_TOKEN: # Добавил проверку, она критична!
    raise ValueError("❌ Ошибка: переменная окружения GATEWAY_BOT_SECRET не задана!")

# ===================================================================
# ⚡️ КЭШ И ВРЕМЕННОЕ ХРАНИЛИЩЕ (Redis) - ЛОКАЛЬНЫЙ ДЛЯ DISCORD БОТА
# ===================================================================
REDIS_BOT_LOCAL_HOST = os.getenv("REDIS_BOT_LOCAL_HOST")
REDIS_BOT_LOCAL_PORT = os.getenv("REDIS_BOT_LOCAL_PORT")
REDIS_BOT_LOCAL_PASSWORD = os.getenv("REDIS_BOT_LOCAL_PASSWORD", "")
REDIS_BOT_LOCAL_POOL_SIZE = int(os.getenv("REDIS_BOT_LOCAL_POOL_SIZE", 10))

REDIS_BOT_LOCAL_URL = os.getenv("REDIS_BOT_LOCAL_URL")
if not REDIS_BOT_LOCAL_URL:
    if REDIS_BOT_LOCAL_HOST and REDIS_BOT_LOCAL_PORT:
        password_part = f":{REDIS_BOT_LOCAL_PASSWORD}" if REDIS_BOT_LOCAL_PASSWORD else ""
        REDIS_BOT_LOCAL_URL = f"redis://{password_part}@{REDIS_BOT_LOCAL_HOST}:{REDIS_BOT_LOCAL_PORT}/0"
    else:
        raise ValueError("❌ Ошибка: REDIS_BOT_LOCAL_URL или REDIS_BOT_LOCAL_HOST/PORT не заданы для Discord-бота!")

# --- Discord-бот (Основные настройки) ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("❌ Ошибка: переменная окружения DISCORD_TOKEN не задана!")

BOT_PREFIX = os.getenv("BOT_PREFIX")

# Настройки для взаимодействия с Discord API (API лимиты, таймауты и т.д.)
MAX_RETRIES_PER_ROLE = int(os.getenv("MAX_RETRIES_PER_ROLE", 2))
INITIAL_SHORT_PAUSE = float(os.getenv("INITIAL_SHORT_PAUSE", 0.1))
RATE_LIMIT_PAUSE = int(os.getenv("RATE_LIMIT_PAUSE", 10))
CREATION_TIMEOUT = int(os.getenv("CREATION_TIMEOUT", 60))
MAX_RETRY_SLEEP = int(os.getenv("MAX_RETRY_SLEEP", 60))


BOT_NAME_FOR_GATEWAY = "test_ordobot_instance_1"