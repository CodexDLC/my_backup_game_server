Архитектура и компоненты проекта

1. Общий обзор

Проект разделён на четыре сервиса:

shared/ — общий пакет с моделями и утилитами; устанавливается в editable-режиме и импортируется в другие сервисы.

bot-service/ — Discord-бот, предоставляет интерфейс игрокам.

game-server/ — основной сервер игрового мира: HTTP/WebSocket API, фоновая обработка.

website/ — веб-интерфейс (Flask), будущая основа клиентской части.

2. Сервис bot-service

Язык/фреймворки: Python, discord.py, python-dotenv.

Работа с БД: SQLAlchemy, asyncpg, psycopg2-binary.

Логирование: colorlog.

Структура:

Discord_API/ — код бота (cogs, команды, события, утилиты).

configs/ — orderbot_config.py, logging_config.py.

requirements.txt — зависимости сервиса.

Запуск:

source .venv/bin/activate
pip install -r bot-service/requirements.txt
python bot-service/Discord_API/main.py

3. Сервис game-server

Язык/фреймворки: Python, FastAPI (HTTP + WebSockets), Uvicorn.

БД: PostgreSQL (через asyncpg/psycopg2-binary).

Кэш и очередь: Redis, Celery (celery[redis]).

Структура:

api/ — main.py, роутеры (routers/world.py и др.), Pydantic-схемы.

world_system/ — модули доступа к БД (server_db/), утилиты (database_utils.py, update_inits.py).

storage/ — redis_client.py, Celery-задания (tasks/).

configs/ — настройки подключения к БД и Redis.

requirements.txt — зависимости сервиса.

Запуск:

source .venv/bin/activate
pip install -r game-server/requirements.txt
uvicorn game-server.api.main:app --reload --host 0.0.0.0 --port 8000

4. Клиентский сайт (website)

Язык/фреймворк: Python, Flask.

Структура:

app.py, routes.py, templates/, static/.

requirements.txt для зависимостей.

Запуск:

source .venv/bin/activate
pip install -r website/requirements.txt
flask run

5. Инфраструктура и окружение

Виртуальное окружение: python3 -m venv .venv в корне проекта.

Docker (в перспективе):

bot-service/Dockerfile, game-server/Dockerfile, docker-compose.yml (Postgres, Redis, Celery, API).

CI/CD: (планируется) автоматическая сборка и развёртывание сервиса на сервере.

6. Системные требования (пример)

ОС сервера: Ubuntu 22.04 LTS

CPU: минимум 2 vCPU

RAM: 4–8 GB

Диск: SSD, минимум 50 GB

Дополнительно: установлен Python 3.11, Docker, Redis, PostgreSQL.

