
# 🎮 NEW_ORDER_RPG: Проект Игрового Сервера (Discord RPG)

## 🚀 Обзор Проекта

NEW_ORDER_RPG — это амбициозный проект игрового сервера для Discord RPG бота, разработанный с использованием современной микросервисной архитектуры. Цель проекта — создать высокопроизводительную, масштабируемую и надежную платформу для многопользовательской ролевой игры, доступной через Discord, веб-клиент и полноценный клиент на Unreal Engine.

Мы стремимся к чистому разделению ответственности, модульности и горизонтальной масштабируемости, чтобы обеспечить стабильную работу даже при высокой нагрузке.

## 🏗️ Микросервисная Архитектура

Архитектура проекта построена на принципах микросервисов, разделенных на логические слои для обеспечения чистоты кода, независимого развертывания и масштабирования.

### Схема Архитектуры

```mermaid
graph TD
    A[Unreal Engine Client] -->|WebSockets/Protobuf| FG(FastAPI Gateway)
    W[Web Client] -->|HTTP/WebSockets| FG
    D[Discord Bot] -->|HTTP/WebSockets/MsgPack| FG

    FG -->|Команды (Redis Command Bus)| RB(Redis)

    subgraph Application Layer (Микросервисы)
        RB --> C[Character Service]
        RB --> Co[Combat Service]
        RB --> I[Inventory Service]
        RB --> Ws[World Service]
    end

    subgraph Domain Layer (Бизнес-логика)
        C --> CDL[Character Domain Logic]
        Co --> CoDL[Combat Domain Logic]
        I --> IDL[Inventory Domain Logic]
        Ws --> WsDL[World Domain Logic]
    end

    subgraph Core Services (Кросс-доменные утилиты)
        CDL --> RS(RandomService)
        CoDL --> RS
        IDL --> RS
        WsDL --> RS
    end

    subgraph Infrastructure Layer (Доступ к данным)
        CDL --> CM(Cache Manager)
        CoDL --> CM
        IDL --> CM
        WsDL --> CM

        CM --> M[MongoDB]
        CM --> P[PostgreSQL]
        CM --> R[Redis]
    end

    subgraph ARQ Workers (Тяжелые задачи)
        RB --&gt;|Задачи| AQ(ARQ Queue)
        AQ --> HTW[Heavy Task Worker]
        AQ --> PTW[Periodic Task Worker]

        HTW --> WsDL
        PTW --> WsDL
    end

    M --&gt;|Консистентность| P
Пояснение Архитектурных Слоев:
API Gateway (FastAPI): Единая точка входа для всех клиентских запросов. Выполняет маршрутизацию и валидацию, преобразует запросы в команды и отправляет их в Redis Command Bus. Не содержит бизнес-логики.
Redis Command Bus: Центральный брокер сообщений для внутренней коммуникации между микросервисами. Обеспечивает асинхронную и надежную доставку команд.
Application Layer (Микросервисы):
Каждый сервис работает в своем Docker-контейнере.
Слушают свои специфичные очереди в Redis.
Отвечают за конкретные функциональные области (персонажи, бой, инвентарь, мир).
Легкие задачи выполняют самостоятельно.
Тяжелые задачи отправляют в ARQ Workers.
Могут запускать автономные периодические задачи ("жизнь сервера").
Domain Layer: Содержит чистую бизнес-логику для каждой доменной области. Не зависит от инфраструктурных деталей.
Core Services: Набор кросс-доменных утилит (например, RandomService, NameGenerator), используемых как в Application, так и в Domain слоях.
Infrastructure Layer: Предоставляет унифицированные интерфейсы для доступа к данным и внешним системам. Инкапсулирует работу с PostgreSQL, MongoDB и Redis, обеспечивая прозрачность для вышележащих слоев.
ARQ Workers: Отдельные сервисы, предназначенные для выполнения асинхронных, ресурсоемких задач. Получают задачи из очереди ARQ и масштабируются независимо.
⚙️ Технологический Стек
Backend & Microservices:
Язык программирования: Python
Web Framework: FastAPI (для API Gateway)
Discord API: discord.py
Асинхронные задачи: ARQ (с Redis как брокером)
ORM: SQLAlchemy (для PostgreSQL)
MongoDB Driver: Motor (асинхронный драйвер)
Оптимизация вычислений: Numba, NumPy
Планирование задач: APScheduler
Клиенты:
Discord Bot: Взаимодействие через discord.py.
Web Client: Фронтенд, взаимодействующий через FastAPI Gateway.
Game Client: Unreal Engine (C++/Blueprints), взаимодействующий через FastAPI Gateway.
Базы данных:
PostgreSQL: Основное хранилище для стабильных данных (пользователи, статистика, основные конфигурации).
MongoDB: Гибкое хранилище для динамических данных (инвентарь, квесты, состояние игрового мира).
Redis: Используется как высокоскоростной кеш, брокер для ARQ и Redis Command Bus.
Сериализация данных:
Внутренняя: MsgPack (для эффективной бинарной передачи между сервисами).
Внешняя: Protobuf (для эффективной бинарной передачи между сервером и клиентами Unreal Engine).
Контейнеризация: Docker (оркестрация через docker-compose.yml).
Миграции БД: Alembic.
Мониторинг (планируется): Prometheus.
📂 Структура Проекта
📦NEW_ORDER_RPG/ (Корневая директория проекта)
┣ 📂.github/        # Конфигурации GitHub Actions/Workflows
┣ 📂.vscode/       # Конфигурации VS Code
┣ 📂alembic/        # Скрипты миграции базы данных (Alembic)
┣ 📂Discord_API/    # Исходный код Discord бота (discord.py)
┣ 📂doc/            # Документация по проекту
┣ 📂game_server/    # Основной код игрового ядра / Application Layer микросервисов (включает логику, разделенную по доменам)
┣ 📂logs/           # Директория для лог-файлов
┣ 📂services_config/ # Docker-конфигурации для каждого сервиса
┃ ┣ 📂worker/        # Dockerfile для ARQ Workers
┃ ┃ ┗ 📜Dockerfile
┃ ┣ 📂Discord_API/   # Dockerfile для Discord бота
┃ ┃ ┗ 📜Dockerfile
┃ ┣ 📂game_server/   # Dockerfile для сервисов из game_server/
┃ ┃ ┗ 📜Dockerfile
┃ ┣ 📂rest_api/      # Dockerfile для REST API / FastAPI Gateway
┃ ┃ ┗ 📜Dockerfile
┃ ┗ 📜__init__.py
┣ 📂venv/           # Виртуальное окружение Python
┣ 📂website/        # Исходный код веб-клиента/фронтенда
┣ 📜.dockerignore    # Файлы и директории для игнорирования при сборке Docker-образов
┣ 📜.env            # Файл переменных окружения (копировать из .env.example)
┣ 📜.gitignore      # Файлы и директории для игнорирования Git
┣ 📜alembic.ini     # Конфигурационный файл Alembic
┣ 📜docker-compose.yml # Главный файл Docker Compose для оркестрации всех сервисов
┣ 📜prometheus.yml  # Конфигурационный файл Prometheus (для мониторинга)
┣ 📜query           # (Предположительно, директория для SQL-запросов или связанных скриптов)
┣ 📜README.md       # Этот файл
┣ 📜redis.conf      # Конфигурация Redis
┣ 📜redis.env       # Переменные окружения для Redis
┣ 📜requirements.txt # Общий файл зависимостей Python (планируется разделение по сервисам)
🚀 Запуск Проекта (Через Docker Compose)
Проект разработан для запуска в Docker-контейнерах. docker-compose.yml в корне проекта оркестрирует все необходимые сервисы.

1. Требования
Docker Desktop (или Docker Engine и Docker Compose)
Git
2. Установка
Клонируйте репозиторий:

Bash

git clone [https://github.com/your-org/NEW_ORDER_RPG.git](https://github.com/your-org/NEW_ORDER_RPG.git)
cd NEW_ORDER_RPG
(Замените https://github.com/your-org/NEW_ORDER_RPG.git на актуальный URL вашего репозитория.)

Настройте переменные окружения:
Скопируйте .env.example в .env и заполните необходимые значения, такие как токены Discord, URL баз данных и т.д.

Bash

cp .env.example .env
# Откройте .env файл в редакторе и заполните его
3. Запуск Сервисов
Запустите все сервисы с помощью Docker Compose:

Bash

docker-compose --env-file .env up -d --build
--env-file .env: Указывает Docker Compose использовать переменные из вашего .env файла.
up: Запускает контейнеры.
-d: Запускает контейнеры в фоновом режиме (detached mode).
--build: Пересобирает образы перед запуском, если есть изменения в Dockerfile или контексте.
4. Проверка состояния сервисов
Bash

docker-compose ps
5. Остановка сервисов
Bash

docker-compose down
🤝 Взаимодействие и API
Discord Bot: Основной интерфейс взаимодействия для игроков через Discord команды и интерактивные элементы.
Web Client: Предоставляет пользовательский интерфейс для управления аккаунтом, просмотра статистики и т.д.
Unreal Engine Client: Полноценный игровой клиент для погружения в мир RPG.
FastAPI Gateway: Единая точка доступа для всех клиентов. Взаимодействия с ним происходят по REST (HTTP) и WebSockets.
Более подробная документация по конкретным эндпоинтам API и взаимодействиям будет предоставлена в директории doc/ и/или через автоматическую документацию FastAPI (Swagger UI/ReDoc).

