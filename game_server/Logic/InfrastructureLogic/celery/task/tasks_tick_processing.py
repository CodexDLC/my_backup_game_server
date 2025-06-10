# game_server/Logic/InfrastructureLogic/celery/task/tasks_tick_processing.py

import asyncio
import logging
from celery import Celery
from typing import Dict, List, Any, Optional

# Импортируем наш логгер
from game_server.services.logging.logging_setup import logger as logger_celery

# Импортируем TickCacheManager для получения батчей из Redis
from game_server.Logic.InfrastructureLogic.app_cache.services.tick_cache_manager import tick_cache_manager

# Предполагается, что у вас есть экземпляр Celery App
from game_server.Logic.InfrastructureLogic.celery.celery_app import app 

# 🔥 НОВОЕ ИЗМЕНЕНИЕ: Импортируем глобальный экземпляр CentralRedisClient 🔥
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client

# � НОВЫЕ ИМПОРТЫ ДЛЯ ОБРАБОТКИ ЛОГИКИ ТИКОВ 🔥
# Здесь вы импортируете классы/функции, которые будут выполнять реальную работу
# Например, если у вас есть сервис, который обрабатывает тренировки, исследования и крафтинг:
# from game_server.Logic.ApplicationLogic.game_logic.tick_handlers import TickLogicHandler 
# Или если у вас функции для каждого типа:
# from game_server.Logic.ApplicationLogic.game_logic.training_tick_processor import process_training_tick
# from game_server.Logic.ApplicationLogic.game_logic.exploration_tick_processor import process_exploration_tick
# from game_server.Logic.ApplicationLogic.game_logic.crafting_tick_processor import process_crafting_tick


class MockTickLogicHandler:
    async def handle_instruction(self, character_id: int, task_type: str, instruction_details: str, full_instruction_data: Dict[str, Any]):
        logger_celery.debug(f"Executing real logic for Character ID: {character_id}, Type: {task_type}, Details: '{instruction_details}'")
        # Здесь будет код, который изменяет состояние персонажа, взаимодействует с другими системами и т.д.
        
        # 🔥 Имитация работы: задержка в 1 секунду 🔥
        await asyncio.sleep(1) 
        
        logger_celery.debug(f"☑️ Celery: Инструкция для Character ID: {character_id} обработана (имитация 1с).")


# 🔥 ИЗМЕНЕНИЕ: Возвращаем функцию Celery-задачи к синхронной (`def`) 🔥
@app.task(bind=True, default_retry_delay=5, max_retries=3)
def process_tick_batch_task(self, category: str, batch_id: str):
    """
    Celery-задача для обработки батча тиковых инструкций.
    Запускает асинхронную логику с помощью asyncio.run().
    """
    logger_celery.info(f"🚀 Celery: Получена задача на обработку батча тиков '{batch_id}' для категории '{category}'.")
    try:
        asyncio.run(
            _run_async_tick_task_logic(self, category, batch_id)
        )
        logger_celery.info(f"🏁 Celery: Обработка всех инструкций в батче '{batch_id}' завершена успешно.")
    except Exception as e:
        logger_celery.error(f"❌ Celery: Ошибка при обработке батча тиков '{batch_id}' ({category}): {str(e)}", exc_info=True)
        # 🔥 ИСПРАВЛЕНИЕ: Добавляем повторную попытку Celery 🔥
        raise self.retry(exc=e)


# 🔥 НОВАЯ АСИНХРОННАЯ ФУНКЦИЯ ДЛЯ ЛОГИКИ ТИКОВ 🔥
async def _run_async_tick_task_logic(self, category: str, batch_id: str):
    """
    Асинхронная логика задачи по обработке тиковых инструкций.
    Переинициализирует глобальный Redis-клиент для текущего Event Loop.
    """
    try:
        # 🔥 ИЗМЕНЕНИЕ: Переинициализируем соединение Redis для текущего Event Loop 🔥
        await central_redis_client.reinitialize_connection()

        instructions_batch = await tick_cache_manager.get_batch_by_id(category, batch_id)

        if not instructions_batch:
            logger_celery.error(f"❌ Celery: Батч '{batch_id}' в категории '{category}' не найден в Redis. Возможно, он истек по TTL или был удален.")
            return

        logger_celery.info(f"✅ Celery: Батч '{batch_id}' ({category}) извлечен из Redis. Содержит {len(instructions_batch)} инструкций.")
        
        # Инициализируем обработчик логики
        logic_handler = MockTickLogicHandler() 

        for instruction in instructions_batch:
            character_id = instruction.get('character_id')
            task_type = instruction.get('task_type')
            instruction_details = instruction.get('instruction_details')
            
            logger_celery.info(f"⚙️ Celery: Обработка инструкции для Character ID: {character_id}, Type: {task_type}, Details: '{instruction_details}'")

            # 🔥🔥🔥 ВЫЗОВ ВАШЕЙ РЕАЛЬНОЙ ЛОГИКИ ТИКОВ 🔥🔥🔥
            await logic_handler.handle_instruction(character_id, task_type, instruction_details, instruction)

            logger_celery.debug(f"☑️ Celery: Инструкция для Character ID: {character_id} обработана.")

        await tick_cache_manager.remove_batch_by_id(category, batch_id)
        logger_celery.info(f"🗑️ Celery: Батч '{batch_id}' удален из Redis после успешной обработки.")

    except Exception as e:
        logger_celery.error(f"❌ Celery: Ошибка во внутренней асинхронной логике тиков: {str(e)}", exc_info=True)
        raise e # Пробрасываем, чтобы внешний except в process_tick_batch_task мог его обработать
