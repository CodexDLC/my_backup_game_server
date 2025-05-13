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
* [API](#api)

---

## Требования

* Python 3.8+
* Redis (локально или через Docker)
* Celery
* PostgreSQL (для хранения основной БД)

---

## Установка

1. Клонируйте репозиторий и перейдите в него:

   ```bash
   git clone https://github.com/your-org/new_order_rpg.git
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

| Переменная                 | Описание                                                         | Пример                                            |
| -------------------------- | ---------------------------------------------------------------- | ------------------------------------------------- |
| `DISCORD_TOKEN`            | Токен вашего Discord-бота                                        | `MTM2...`                                         |
| `BOT_PREFIX`               | Префикс команд бота                                              | `!`                                               |
| `GAME_SERVER_API`          | Базовый URL HTTP API сервера                                     | `http://localhost:8000`                           |
| `DATABASE_URL`             | SQLAlchemy URL для подключения к PostgreSQL                      | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `REDIS_URL`                | URL подключения к Redis (используется Celery и кеш)              | `redis://redis:6379/0`                            |
| `RANDOM_POOL_SIZE`         | Размер пула случайных элементов, загружаемого при старте сервиса | `65535`                                           |
| `RANDOM_POOL_THRESHOLD`    | Минимальный порог элементов в пуле для авто-рестока              | `10`                                              |
| `CELERY_BROKER_URL`        | URL брокера задач Celery (обычно совпадает с `REDIS_URL`)        | `${REDIS_URL}`                                    |
| `CELERY_RESULT_BACKEND`    | URL для хранения результатов Celery                              | `${REDIS_URL}`                                    |
| `TICK_INTERVAL_SECONDS`    | Интервал глобального тика сервера (в секундах)                   | `60`                                              |
| `TICK_XP_INTERVAL_SECONDS` | Интервал тика начисления опыта (в секундах)                      | `600`                                             |

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

> Периодические задачи, такие как глобальный тик, будут выполняться по расписанию.

---

## Запуск приложения

```bash
uvicorn game_server.api.main:app --reload
```

Сервер доступен по адресу `http://127.0.0.1:8000` (или `GAME_SERVER_API`).

---

## Запуск через Docker Compose

В корне проекта есть файл `docker-compose.yml`, который поднимает основные сервисы:

* **redis** — сервер Redis на порту `6379`.
* **fastapi** — приложение FastAPI на порту `8000`.
* **celery** — Celery worker (команда `celery -A game_server.storage.celery_app worker --loglevel=info`).
* **prometheus** — Prometheus мониторинг на порту `9090`.

Запустите все сервисы одной командой:

```bash
docker-compose up -d
```

Окружение читается из `.env`, переменные `CELERY_BROKER_URL` и `REDIS_URL` задаются автоматически по конфигу.

---

## API

### GET `/random/next`

Возвращает следующий случайный элемент из заранее загруженного пула.

**Параметры запроса:**

* `pool_size` (integer, optional) — размер пула. По умолчанию `RANDOM_POOL_SIZE`.

**Примеры:**

```bash
# Без параметров, используется RANDOM_POOL_SIZE
curl "${GAME_SERVER_API}/random/next"
```

```json
{ "value": "some_random_item" }
```

```bash
# С указанием размера пула
curl "${GAME_SERVER_API}/random/next?pool_size=500"
```

```json
{ "value": "another_random_item" }
```

---

README обновлён с учётом запуска через Docker Compose и детальными инструкциями для всех сервисов.
