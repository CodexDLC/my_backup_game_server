# Устанавливаем официальный Python как базовый образ
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем файлы проекта
COPY game_server /app/game_server
COPY . /app
COPY .env /app/.env

# Устанавливаем переменную окружения
ENV PYTHONPATH=/app


# Открываем порт 8000 для FastAPI
EXPOSE 8000



