import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# ===================================================================
# 🔑 ОБЩИЕ НАСТРОЙКИ ПРИЛОЖЕНИЯ
# ===================================================================
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# API Сервер
PUBLIC_GAME_SERVER_API = os.getenv("PUBLIC_GAME_SERVER_API")
INTERNAL_GAME_SERVER_API = os.getenv("INTERNAL_GAME_SERVER_API")
GAME_SERVER_API = os.getenv("GAME_SERVER_API")
RANDOM_API_URL = os.getenv("RANDOM_API_URL")
REGISTRATION_URL = os.getenv("REGISTRATION_URL")

BOT_GATEWAY_SECRET = os.getenv("GATEWAY_BOT_SECRET")
# ===================================================================
# 🐘 БАЗА ДАННЫХ (PostgreSQL)
# ===================================================================
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL_SYNC должен быть определен, только если DATABASE_URL уже задан
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")
if DATABASE_URL_SYNC is None and DATABASE_URL is not None:
    DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "")

SQL_ECHO = os.getenv("SQL_ECHO", "False").lower() in ("true", "1", "yes")


MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "youruser")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "yourpassword")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "game_db_mongo")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_HOST_LOCAL = os.getenv("MONGO_HOST_LOCAL", "127.0.0.1")
MONGO_HOST_CONTAINER = os.getenv("MONGO_HOST_CONTAINER", "mongo_db")

# ===================================================================
# ⚡️ КЭШ И ВРЕМЕННОЕ ХРАНИЛИЩЕ (Redis) - ЦЕНТРАЛЬНЫЙ СЕРВЕР
# ===================================================================
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
if not REDIS_PASSWORD:
    raise ValueError("❌ Ошибка: переменная окружения REDIS_PASSWORD не задана для центрального Redis!")

REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", 40))

# URL'ы для центрального Redis (основная БД и кэш)
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"  # Основная БД Redis
REDIS_CACHE_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1" # Кэш-БД Redis (например, БД 1)

REDIS_BOT_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/9" # БД Redis для бота (db: 9)

# ===================================================================
# 🐇 БРОКЕР СООБЩЕНИЙ (RabbitMQ)
# ===================================================================
# Переменные для построения AMQP_URL
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/") # Указываем значение по умолчанию, если не задано

# Формирование AMQP_URL
# Важно: если в пароле есть спецсимволы, их нужно URL-кодировать.
# Если AMQP_URL уже задан напрямую в .env, используем его, иначе формируем
AMQP_URL = os.getenv("AMQP_URL")
if not AMQP_URL:
    if all([RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_VHOST is not None]):
        # Убедитесь, что vhost начинается с '/', если это не просто '/'
        # Некоторые библиотеки могут некорректно обрабатывать DSN без начального слэша
        # if not RABBITMQ_VHOST.startswith('/'):
        #     RABBITMQ_VHOST = '/' + RABBITMQ_VHOST
        AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}{RABBITMQ_VHOST}"
    else:
        # Можно сделать это ошибкой или оставить AMQP_URL None, в зависимости от логики вашего приложения
        print("❌ Предупреждение: Не все переменные окружения RabbitMQ заданы. AMQP_URL не будет сформирован автоматически.")
        AMQP_URL = None # Установите None или вызовите исключение

# Если AMQP_URL критичен для работы приложения, можете добавить проверку:
# if not AMQP_URL:
#     raise ValueError("❌ Ошибка: переменная окружения AMQP_URL или необходимые переменные RabbitMQ не заданы!")

GATEWAY_BOT_SECRET = os.getenv("GATEWAY_BOT_SECRET")