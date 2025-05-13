# New Order RPG — Документация

Проект игрового сервера для Discord-RPG бота с генератором случайных элементов из пула и фоновой обработкой задач через Celery и Redis.

## Содержание

* [Требования](#требования)
* [Установка](#установка)
* [Переменные окружения](#переменные-окружения)
* [Запуск Redis](#запуск-redis)
* [Запуск Celery](#запуск-celery)
* [Запуск приложения](#запуск-приложения)
* [Запуск через Docker Compose](#запуск-через-docker-compose)
* [Локальные и публичные адреса](#локальные-и-публичные-адреса)
* [API](#api)

---

## Требования

* Python 3.8+
* Redis (локально или через Docker)
* Celery
* PostgreSQL

---

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone git@github.com:your-org/new_order_rpg.git
   cd new_order_rpg
   ```
2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```
3. Скопируйте шаблон окружения и заполните свои значения:

   ```bash
   cp .env.example .env
   ```

---

## Переменные окружения

Файл `.env` в корне проекта содержит следующие переменные:

```ini
# Discord-бот
DISCORD_TOKEN=MTM2MTA3NTgyNjU4NTYzMjc2OA.G4pHmT...  # токен бота
BOT_PREFIX=!                                     # префикс команд

# HTTP API (устаревшая переменная, используется в части кода)
GAME_SERVER_API=http://localhost:8000            # legacy-константа для API

# Публичный и внутренний адреса
PUBLIC_GAME_SERVER_API=https://api.yourdomain.com
INTERNAL_GAME_SERVER_API=http://fastapi:8000      # имя сервиса из docker-compose

# PostgreSQL
DB_NAME=game_db
DB_USER=codexen
DB_PASSWORD=123
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis и пул генерации
REDIS_URL=redis://redis:6379/0
RANDOM_POOL_SIZE=65535
RANDOM_POOL_THRESHOLD=10

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Интервалы тиков (в секундах)
TICK_INTERVAL_SECONDS=60
TICK_XP_INTERVAL_SECONDS=600
```

---

## Запуск Redis

**Локально (если Redis установлен):**

```bash
redis-server --daemonize yes
```

**Через Docker:**

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

---

## Запуск Celery

**Worker:**

```bash
celery -A game_server.storage.celery_app worker --loglevel=info
```

**Scheduler (beat):**

```bash
celery -A game_server.storage.celery_app beat --loglevel=info
```

---

## Запуск приложения

```bash
uvicorn game_server.api.main:app --reload
```

Сервер будет доступен по адресу `http://127.0.0.1:8000`.

---

## Запуск через Docker Compose

В файле `docker-compose.yml` настроены сервисы:

* `redis` — Redis на порту 6379.
* `fastapi` — приложение FastAPI на порту 8000.
* `celery` — воркер Celery.
* `prometheus` — мониторинг Prometheus на порту 9090.

Запуск всех сервисов:

```bash
docker-compose --env-file .env up -d --build
```

---

## Локальные и публичные адреса

Проект читает из `.env` два адреса:

* `PUBLIC_GAME_SERVER_API` — адрес, который видят внешние клиенты и вебхуки.
* `INTERNAL_GAME_SERVER_API` — адрес для внутренних вызовов между сервисами (имя контейнера).

Пример использования в коде:

```python
from game_server.config.server_config import get_settings
cfg = get_settings()
PUBLIC_API = cfg.public_api
INTERNAL_API = cfg.internal_api
```

---

## API

### GET `/random/next`

Возвращает следующий случайный элемент из пула.

**Параметры:**

* `pool_size` (integer, optional) — размер пула, по умолчанию `RANDOM_POOL_SIZE`.

**Примеры:**

```bash
curl "${PUBLIC_GAME_SERVER_API}/random/next"
```

```json
{ "value": "some_random_item" }
```

```bash
curl "${PUBLIC_GAME_SERVER_API}/random/next?pool_size=500"
```

```json
{ "value": "another_random_item" }
```

---

*Документация обновлена на основе вашего `.env`.*
