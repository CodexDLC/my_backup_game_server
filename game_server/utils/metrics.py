import time

from game_server.services.logging.logging_setup import logger

from prometheus_client import Histogram
import asyncio  # Добавлено для обработки асинхронных функций

# Инициализация Prometheus-метрики
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Время выполнения запроса', ['endpoint'])

# Настройка логирования


def measure_time(endpoint_name):
    """
    Декоратор для измерения времени выполнения функции.
    Записывает результаты в Prometheus-метрики и лог-файл.
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            """Обработчик для асинхронных функций."""
            start_time = time.time()
            result = await func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            # Запись метрики в Prometheus
            REQUEST_LATENCY.labels(endpoint=endpoint_name).observe(elapsed_time)

            # Запись данных в лог
            logger.info(f"[{endpoint_name}] Выполнено за {elapsed_time:.4f} сек.")

            return result

        def sync_wrapper(*args, **kwargs):
            """Обработчик для синхронных функций."""
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            # Запись метрики в Prometheus
            REQUEST_LATENCY.labels(endpoint=endpoint_name).observe(elapsed_time)

            # Запись данных в лог
            logger.info(f"[{endpoint_name}] Выполнено за {elapsed_time:.4f} сек.")

            return result

        if asyncio.iscoroutinefunction(func):  # Проверяем, является ли функция асинхронной
            return async_wrapper
        return sync_wrapper  # Если нет, используем синхронный обработчик

    return decorator
