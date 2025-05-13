from game_server.task_queue.celery_config import app
from celery_app import celery_app

# Пример задачи: обрабатываем глобальный тик
@app.task
def process_global_tick():
    print("Processing global tick...")
    # Ваша логика обработки тиков
