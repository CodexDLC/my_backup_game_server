import asyncio
import json
from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger

# Импортируем наш новый высокоуровневый менеджер кэша для тиков
from game_server.Logic.InfrastructureLogic.app_cache.services.tick_cache_manager import tick_cache_manager

# Константы BATCH_TASK_TTL_SECONDS и BATCH_REPORT_TTL_SECONDS
# теперь управляются внутри tick_cache_manager, поэтому прямой импорт здесь не критичен,
# но оставим его для ясности, если понадобится для других целей в будущем.
from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import BATCH_TASK_TTL_SECONDS, BATCH_REPORT_TTL_SECONDS


async def process_tasks(redis_client):
    """
    Основная функция для обработки задач.
    Извлекает задачи из Redis-хэшей, используя TickCacheManager.
    На данный момент просто логирует извлеченные задачи.
    В будущем здесь будет вызов Celery-задач.
    
    :param redis_client: Экземпляр CentralRedisClient (хотя в основном
                         будет использоваться tick_cache_manager).
    """
    logger.info("process_tasks: Начинаем извлечение задач из Redis-очередей через TickCacheManager...")

    try:
        # Получаем все категоризированные задачи через TickCacheManager
        # Этот метод уже десериализует JSON и возвращает готовый словарь.
        categorized_tasks = await tick_cache_manager.get_all_categorized_tasks_from_redis()

        if not categorized_tasks:
            logger.info("process_tasks: Нет категоризированных задач для обработки.")
            return

        processed_tasks_count = 0
        
        # Перебираем каждую категорию задач и затем каждую задачу внутри категории
        for category, tasks_for_category in categorized_tasks.items():
            logger.info(f"process_tasks: Обработка категории '{category}' с {len(tasks_for_category)} задачами.")
            
            for character_id_str, task_data in tasks_for_category.items():
                try:
                    logger.info(f"process_tasks: Извлечена задача для {category} - Character ID: {character_id_str}, Task Data: {task_data}")
                    processed_tasks_count += 1
                    
                    # TODO: Здесь в будущем будет вызов Celery-задачи для каждой task_data
                    # Например: celery_app.send_task('tasks.process_character_tick', args=[character_id_str, task_data])

                except Exception as e:
                    logger.error(f"Неожиданная ошибка при обработке задачи для {category}, character_id={character_id_str}: {e}")

        logger.info(f"process_tasks: Завершено извлечение и временная обработка {processed_tasks_count} задач.")

        # Мы полагаемся на TTL, установленный в TickCacheManager, для очистки.
        # Явное удаление здесь не нужно.
        # Если потребуется немедленная очистка после обработки всех задач,
        # можно вызвать await tick_cache_manager.delete_all_categorized_tasks()
        # Однако, в системе с Celery, задачи обычно удаляются по мере их успешной постановки в очередь Celery.

    except Exception as e:
        logger.error(f"❌ Ошибка в process_tasks при работе с TickCacheManager: {str(e)}", exc_info=True)