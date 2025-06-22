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
# Создаем чистый, легковесный и безопасный образ для запуска координаторов.
# ===================================================================
FROM python:3.13-slim-bookworm

WORKDIR /app

# Создаем непривилегированного пользователя для безопасного запуска
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Копируем готовое виртуальное окружение из этапа "Сборщик"
COPY --from=builder /opt/venv /opt/venv

# Копируем код, необходимый для работы координаторов
# Здесь appuser становится владельцем всего /app/game_server
COPY --chown=appuser:appuser ./game_server /app/game_server

# --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Убедимся, что у пользователя appuser есть права на запись в папку логов ---
# Создаем папку для логов, если она еще не создана.
# И СРАЗУ ЖЕ меняем ее владельца на 'appuser', чтобы у него были полные права на запись.
# Это абсолютно критично, так как /app/game_server/logs является точкой монтирования.
RUN mkdir -p /app/game_server/logs && \
    chown -R appuser:appuser /app/game_server/logs
# --- КОНЕЦ КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ---


# Переключаемся на непривилегированного пользователя
USER appuser

# Активируем виртуальное окружение
ENV PATH="/opt/venv/bin:$PATH"

# Указываем команду по умолчанию (будет переопределена в docker-compose.yml)
CMD ["python", "-m", "game_server.Logic.ApplicationLogic.tick_infra.tick_coordinator"]
