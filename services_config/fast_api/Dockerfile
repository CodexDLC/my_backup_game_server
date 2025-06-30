# ===================================================================
# ЭТАП 1: "СБОРЩИК" (Builder)
# Устанавливаем зависимости, включая те, что требуют компиляции.
# ===================================================================
FROM python:3.13-slim-bookworm AS builder

# Устанавливаем системные зависимости, необходимые для компиляции C-расширений
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаем виртуальное окружение для чистой установки
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Обновляем pip и устанавливаем wheel
RUN pip install --upgrade pip wheel

# Копируем и устанавливаем зависимости
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ===================================================================
# ЭТАП 2: "ФИНАЛЬНЫЙ ОБРАЗ" (Final)
# Создаем чистый, легковесный и безопасный образ для запуска API.
# ===================================================================
FROM python:3.13-slim-bookworm

# --- РЕШЕНИЕ: Устанавливаем curl для healthcheck ---
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаем непривилегированного пользователя для безопасного запуска
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Копируем готовое виртуальное окружение из этапа "Сборщик"
COPY --from=builder /opt/venv /opt/venv

# Копируем код, необходимый для работы API
COPY --chown=appuser:appuser ./game_server /app/game_server

# Переключаемся на непривилегированного пользователя
USER appuser

# Активируем виртуальное окружение
ENV PATH="/opt/venv/bin:$PATH"

# Сообщаем Docker, что контейнер будет слушать этот порт
EXPOSE 8000

# ВАЖНО: Команда запуска сейчас должна указывать на debug_app.py для теста!
# Когда мы закончим, мы вернем ее к вашему основному приложению.
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "3", "-b", "0.0.0.0:8000", "game_server.api_rest.main:app"]
