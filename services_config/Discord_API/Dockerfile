# ===================================================================
# ЭТАП 1: "СБОРЩИК" (Builder)
# Устанавливаем зависимости в изолированной среде.
# ===================================================================
# Используем конкретную и стабильную версию Python
FROM python:3.12-slim-bookworm AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем виртуальное окружение для чистой установки
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Обновляем pip и устанавливаем wheel для ускорения сборки
RUN pip install --upgrade pip wheel

# Копируем файл с зависимостями бота для кэширования этого слоя
# ИСПРАВЛЕНИЕ: Изменена путь к requirements.txt
COPY ./game_server/app_discord_bot/requirements.txt .

# Устанавливаем зависимости в виртуальное окружение
RUN pip install --no-cache-dir -r requirements.txt


# ===================================================================
# ЭТАП 2: "ФИНАЛЬНЫЙ ОБРАЗ" (Final)
# Создаем чистый, легковесный и безопасный образ для запуска.
# ===================================================================
FROM python:3.12-slim-bookworm

WORKDIR /app

# Создаем непривилегированного пользователя для безопасного запуска
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Копируем готовое виртуальное окружение из этапа "Сборщик"
COPY --from=builder /opt/venv /opt/venv

# Копируем код, необходимый для работы координаторов
# Здесь appuser становится владельцем всего /app/game_server
COPY --chown=appuser:appuser ./game_server /app/game_server


# Переключаемся на непривилегированного пользователя
USER appuser

# Активируем виртуальное окружение для всех последующих команд
ENV PATH="/opt/venv/bin:$PATH"

# Указываем команду для запуска сервиса
CMD ["python", "-m", "Discord_API.main"]