# Используем официальный Python как базовый образ
FROM python:3.13.3

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt /app/requirements.txt

# Копируем папку с кодом
COPY game_server /app/game_server
COPY . /app

# Устанавливаем переменную окружения
ENV PYTHONPATH=/app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Открываем порт 8000 для FastAPI
EXPOSE 8000

# Запускаем FastAPI сервер
CMD ["uvicorn", "game_server.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
