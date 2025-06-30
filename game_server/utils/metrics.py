import time
from game_server.config.logging.logging_setup import app_logger as logger
from prometheus_client import Histogram, Counter # Добавлен Counter для ошибок
import asyncio

# Инициализация Prometheus-метрики
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Время выполнения запроса', ['endpoint', 'status']) # Добавлена метка 'status'
REQUEST_ERRORS_TOTAL = Counter('request_errors_total', 'Общее количество ошибок запросов', ['endpoint']) # Новая метрика для ошибок


def measure_time(endpoint_name):
    """
    Декоратор для измерения времени выполнения функции.
    Записывает результаты в Prometheus-метрики и лог-файл.
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            """Обработчик для асинхронных функций."""
            start_time = time.perf_counter() # ✅ ИЗМЕНЕНО: Используем time.perf_counter()
            status = "success" # По умолчанию успешный статус
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error" # Статус ошибки при исключении
                REQUEST_ERRORS_TOTAL.labels(endpoint=endpoint_name).inc() # Увеличиваем счетчик ошибок
                logger.error(f"[{endpoint_name}] Ошибка выполнения: {e}")
                raise # Повторно выбрасываем исключение
            finally:
                elapsed_time = time.perf_counter() - start_time # ✅ ИЗМЕНЕНО: Используем time.perf_counter()
                # Запись метрики в Prometheus, теперь с меткой статуса
                REQUEST_LATENCY.labels(endpoint=endpoint_name, status=status).observe(elapsed_time)
                # Запись данных в лог
                logger.info(f"[{endpoint_name}] Выполнено со статусом {status} за {elapsed_time:.4f} сек.")

        def sync_wrapper(*args, **kwargs):
            """Обработчик для синхронных функций."""
            start_time = time.perf_counter() # ✅ ИЗМЕНЕНО: Используем time.perf_counter()
            status = "success" # По умолчанию успешный статус
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error" # Статус ошибки при исключении
                REQUEST_ERRORS_TOTAL.labels(endpoint=endpoint_name).inc() # Увеличиваем счетчик ошибок
                logger.error(f"[{endpoint_name}] Ошибка выполнения: {e}")
                raise # Повторно выбрасываем исключение
            finally:
                elapsed_time = time.perf_counter() - start_time # ✅ ИЗМЕНЕНО: Используем time.perf_counter()
                # Запись метрики в Prometheus, теперь с меткой статуса
                REQUEST_LATENCY.labels(endpoint=endpoint_name, status=status).observe(elapsed_time)
                # Запись данных в лог
                logger.info(f"[{endpoint_name}] Выполнено со статусом {status} за {elapsed_time:.4f} сек.")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

# Пример использования (для иллюстрации)
# from prometheus_client import start_http_server
# import random

# @measure_time("my_async_operation")
# async def some_async_task():
#     await asyncio.sleep(random.uniform(0.01, 0.5))
#     if random.random() < 0.1: # 10% шанс ошибки
#         raise ValueError("Случайная ошибка в асинхронной задаче!")
#     return "Async done"

# @measure_time("my_sync_operation")
# def some_sync_task():
#     time.sleep(random.uniform(0.005, 0.2))
#     if random.random() < 0.05: # 5% шанс ошибки
#         raise TypeError("Случайная ошибка в синхронной задаче!")
#     return "Sync done"

# async def main():
#     start_http_server(8001) # Запуск Prometheus Exporter на порту 8001
#     logger.info("Prometheus exporter запущен на порту 8001")
#     for _ in range(10):
#         try:
#             await some_async_task()
#         except (ValueError, TypeError):
#             pass # Ловим ошибку, чтобы продолжить выполнение
#         try:
#             some_sync_task()
#         except (ValueError, TypeError):
#             pass # Ловим ошибку, чтобы продолжить выполнение
#     await asyncio.sleep(5) # Даем время на сбор метрик

# if __name__ == "__main__":
#     # Убедитесь, что logging_setup корректно инициализирован здесь, если запускаете напрямую
#     # logging_setup.configure_logging() 
#     asyncio.run(main())
