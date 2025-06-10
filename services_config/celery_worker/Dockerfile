# ===================================================================
# ЭТАП 1: "СБОРЩИК" (Builder)
# Устанавливаем зависимости в изолированной, чистой среде.
# ===================================================================
# Используем стабильную и легковесную версию Python
FROM python:3.11-slim-bookworm AS builder

# Устанавливаем системные зависимости, необходимые для компиляции
# gcc и python3-dev нужны для сборки C-расширений, таких как librabbitmq
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаем виртуальное окружение, чтобы не засорять системный Python
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Обновляем pip и ставим wheel для ускорения установки пакетов
RUN pip install --upgrade pip wheel

# Копируем файл с зависимостями и устанавливаем их.
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ===================================================================
# ЭТАП 2: "ФИНАЛЬНЫЙ ОБРАЗ" (Final)
# Создаем чистый, легковесный и безопасный образ для запуска воркера.
# ===================================================================
FROM python:3.11-slim-bookworm

WORKDIR /app

# Создаем непривилегированного пользователя для безопасного запуска
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Копируем ТОЛЬКО готовое виртуальное окружение из этапа "Сборщик"
COPY --from=builder /opt/venv /opt/venv

# Воркеру нужен доступ к коду, где определены задачи (в вашем случае, в 'game_server').
COPY --chown=appuser:appuser ./game_server /app/game_server

# Переключаемся на непривилегированного пользователя
USER appuser

# Активируем виртуальное окружение для всех последующих команд
ENV PATH="/opt/venv/bin:$PATH"

# Указываем команду для запуска сервиса по умолчанию.
CMD ["celery", "-A", "game_server.Logic.InfrastructureLogic.celery.celery_app", "worker", "--loglevel=info", "-P", "gevent"]
