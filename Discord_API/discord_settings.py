
# Discord_API\discord_settings.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# --- Настройки для API и серверных параметров (Остаются, так как бот будет взаимодействовать с ними) ---
PUBLIC_GAME_SERVER_API = os.getenv("PUBLIC_GAME_SERVER_API")
INTERNAL_GAME_SERVER_API = os.getenv("INTERNAL_GAME_SERVER_API")
GAME_SERVER_API = os.getenv("GAME_SERVER_API") # Возможно, это и есть INTERNAL_GAME_SERVER_API
RANDOM_API_URL = os.getenv("RANDOM_API_URL")

# Явно указываем URL для Backend API, с которым бот будет взаимодействовать.
# В docker-compose это будет http://rest_api:8000
API_URL = os.getenv("REST_API_URL")
if not API_URL:
    raise ValueError("❌ Ошибка: переменная окружения REST_API_URL не задана для Discord-бота!")


# --- Discord-бот (Новый, чистый блок) ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") # Переменная для токена Discord бота
if not DISCORD_TOKEN:
    raise ValueError("❌ Ошибка: переменная окружения DISCORD_BOT_TOKEN не задана!")

BOT_PREFIX = os.getenv("BOT_PREFIX") # Префикс для команд бота

# Настройки для ЛОКАЛЬНОГО REDIS для Discord-бота
# Используется как кэш для UI-контекста и состояния бота
REDIS_BOT_LOCAL_URL = os.getenv("REDIS_BOT_LOCAL_URL")
if not REDIS_BOT_LOCAL_URL:
    raise ValueError("❌ Ошибка: переменная окружения REDIS_BOT_LOCAL_URL не задана для Discord-бота!")

# Если для локального Redis есть пароль, он будет частью URL
# REDIS_BOT_LOCAL_PASSWORD = os.getenv("REDIS_BOT_LOCAL_PASSWORD", "") # Если нужен отдельный пароль для локального
REDIS_BOT_LOCAL_POOL_SIZE = int(os.getenv("REDIS_BOT_LOCAL_POOL_SIZE", 5)) # Пул соединений для локального Redis

# Настройки для взаимодействия с RabbitMQ (если бот напрямую отправляет/слушает сообщения)
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
if not RABBITMQ_URL:
    raise ValueError("❌ Ошибка: переменная окружения RABBITMQ_URL не задана для Discord-бота!")

# Настройки для взаимодействия с Discord API (API лимиты, таймауты и т.д.)
MAX_RETRIES_PER_ROLE = 2
INITIAL_SHORT_PAUSE = 0.1
RATE_LIMIT_PAUSE = 10
CREATION_TIMEOUT = 60
MAX_RETRY_SLEEP = 60