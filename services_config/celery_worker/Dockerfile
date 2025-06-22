# ===================================================================
# ЭТАП 1: "СБОРЩИК" (Builder)
# Устанавливаем зависимости в изолированной, чистой среде.
# ===================================================================
# Рекомендуется использовать одинаковую версию Python на обоих этапах
# для избежания потенциальных проблем с C-расширениями.
FROM python:3.13-slim-bookworm AS builder

# Устанавливаем системные зависимости, необходимые для компиляции
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
# Убедитесь, что arq[redis] есть в requirements.txt
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ===================================================================
# ЭТАП 2: "ФИНАЛЬНЫЙ ОБРАЗ" (Final)
# Создаем чистый, легковесный и безопасный образ для запуска сервисов.
# ===================================================================
FROM python:3.13-slim-bookworm

WORKDIR /app

# Создаем непривилегированного пользователя для безопасного запуска
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Копируем ТОЛЬКО готовое виртуальное окружение из этапа "Сборщик"
COPY --from=builder /opt/venv /opt/venv

# Копируем код нашего приложения
COPY --chown=appuser:appuser ./game_server /app/game_server

# Переключаемся на непривилегированного пользователя
USER appuser

# Активируем виртуальное окружение для всех последующих команд
ENV PATH="/opt/venv/bin:$PATH"

# Указываем команду по умолчанию.
# Она все равно будет переопределена в docker-compose.yml для каждого сервиса,
# но это хорошая практика для отладки.
# Пример для ARQ воркера:
# CMD ["arq", "game_server.worker.WorkerSettings"]
