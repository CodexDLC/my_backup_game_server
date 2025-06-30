# /game_server/api_fast/gateway_dependencies.py

import traceback # 🔥 НОВЫЙ ИМПОРТ для подробной трассировки
from typing import Dict, Any

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus

async def initialize_gateway_dependencies() -> Dict[str, Any]:
    """
    Инициализирует ТОЛЬКО зависимости, необходимые для работы WebSocket шлюза.
    """
    logger.info("--- 🚀 Запуск минимальных зависимостей для шлюза ---")
    dependencies: Dict[str, Any] = {}

    try:
        # Инициализируем и подключаемся к RabbitMQ
        logger.info("Инициализация RabbitMQ Message Bus для шлюза...")
        rabbit_bus_instance = RabbitMQMessageBus()
        await rabbit_bus_instance.connect() # 🔥 ЭТО НАИБОЛЕЕ ВЕРОЯТНАЯ ТОЧКА СБОЯ
        dependencies["message_bus"] = rabbit_bus_instance
        logger.info("✅ RabbitMQ Message Bus для шлюза успешно инициализирован.")

        # logger как зависимость - это немного нетипично, но если вам нужно,
        # чтобы он был доступен через app.state.gateway_dependencies, оставьте.
        dependencies["logger"] = logger
        
        logger.info("--- ✅ Минимальные зависимости для шлюза успешно запущены ---")
        return dependencies

    except Exception as e:
        # 🔥 УЛУЧШЕННОЕ ЛОГИРОВАНИЕ: Выводим полную трассировку
        logger.critical(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к RabbitMQ Message Bus: {e}", exc_info=True)
        logger.critical(f"🚨 Полная трассировка ошибки RabbitMQ: \n{traceback.format_exc()}")
        
        # В случае ошибки пытаемся корректно все закрыть
        await shutdown_gateway_dependencies(dependencies)
        # 🔥 ВАЖНО: Перебрасываем исключение, чтобы lifespan понял, что запуск провалился
        raise RuntimeError("Не удалось запустить шлюз из-за ошибки инициализации зависимостей.") from e

async def shutdown_gateway_dependencies(dependencies: Dict[str, Any]):
    """Централизованно завершает работу минимальных зависимостей шлюза."""
    logger.info("--- 🛑 Остановка минимальных зависимостей шлюза ---")
    
    if "message_bus" in dependencies and dependencies["message_bus"]:
        logger.info("🛑 Закрытие RabbitMQ Message Bus...")
        await dependencies["message_bus"].close()
        logger.info("✅ RabbitMQ Message Bus закрыт.")
    
    logger.info("--- ✅ Минимальные зависимости шлюза корректно остановлены ---")