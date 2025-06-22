# game_server/Logic/InfrastructureLogic/app_cache/services/tick/tick_cache_manager.py

import logging
import json
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod # Добавлено

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.constants.redis import REDIS_COORDINATOR_TASK_HASH, REDIS_TASK_QUEUE_CRAFTING, REDIS_TASK_QUEUE_EXPLORATION, REDIS_TASK_QUEUE_TRAINING
from game_server.config.settings.redis_setting import BATCH_TASK_TTL_SECONDS

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # Изменено

# Импортируем новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_tick_cache import ITickCacheManager # Добавлено


# Изменяем класс TickCacheManager, чтобы он наследовал от ITickCacheManager
class TickCacheManager(ITickCacheManager): # Изменено
    """
    Высокоуровневый менеджер для кэширования и управления задачами тиковой системы в Redis.
    """

    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ TickCacheManager инициализирован.") # Изменено: используем logger

    async def add_batch_of_instructions_to_category(self, category: str, batch_id: str, instructions_batch: List[Dict[str, Any]]):
        """
        Добавляет батч инструкций под уникальным ID в соответствующее поле категории
        в главном хэше REDIS_COORDINATOR_TASK_HASH.
        """
        valid_categories = [REDIS_TASK_QUEUE_EXPLORATION, REDIS_TASK_QUEUE_TRAINING, REDIS_TASK_QUEUE_CRAFTING]
        if category not in valid_categories:
            logger.error(f"Неизвестная категория задачи: {category}")
            return

        current_batches_json = await self.redis.hget(REDIS_COORDINATOR_TASK_HASH, category)
        current_batches = json.loads(current_batches_json) if current_batches_json else {}

        current_batches[batch_id] = instructions_batch

        await self.redis.hset(REDIS_COORDINATOR_TASK_HASH, category, json.dumps(current_batches))
        await self.redis.expire(REDIS_COORDINATOR_TASK_HASH, BATCH_TASK_TTL_SECONDS)
        logger.debug(f"TickCacheManager: Добавлен батч '{batch_id}' с {len(instructions_batch)} инструкциями в категорию '{category}'.")

    async def get_all_categories_with_batches(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Извлекает все категории и все батчи инструкций для каждой категории из Redis.
        """
        logger.info(f"TickCacheManager: Начинаем извлечение всех батчей из '{REDIS_COORDINATOR_TASK_HASH}'...")

        all_categories_raw = await self.redis.hgetall(REDIS_COORDINATOR_TASK_HASH)

        if not all_categories_raw:
            logger.info(f"TickCacheManager: Хэш '{REDIS_COORDINATOR_TASK_HASH}' пуст. Нет батчей для извлечения.")
            return {}

        categorized_batches = {}
        for category_bytes, batches_json_bytes in all_categories_raw.items():
            category = category_bytes.decode('utf-8')
            try:
                batches_for_category = json.loads(batches_json_bytes.decode('utf-8'))

                if isinstance(batches_for_category, dict):
                    categorized_batches[category] = batches_for_category
                    logger.debug(f"TickCacheManager: Извлечено {len(batches_for_category)} батчей для категории '{category}'.")
                else:
                    logger.error(f"TickCacheManager: Неожиданный формат данных для категории '{category}'.")

            except json.JSONDecodeError as e:
                logger.error(f"TickCacheManager: Ошибка десериализации данных для категории '{category}': {e}")
            except UnicodeDecodeError as e:
                logger.error(f"TickCacheManager: Ошибка декодирования Redis-данных для категории '{category}': {e}")


        logger.info(f"TickCacheManager: Завершено извлечение батчей из Redis. Всего категорий с батчами: {len(categorized_batches)}.")
        return categorized_batches

    async def get_batch_by_id(self, category: str, batch_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получает конкретный батч инструкций по его ID из указанной категории.
        """
        current_batches_json_bytes = await self.redis.hget(REDIS_COORDINATOR_TASK_HASH, category)
        if not current_batches_json_bytes:
            logger.debug(f"TickCacheManager: Категория '{category}' не найдена или пуста.")
            return None

        current_batches = json.loads(current_batches_json_bytes.decode('utf-8'))
        batch = current_batches.get(batch_id)

        if batch:
            logger.debug(f"TickCacheManager: Батч '{batch_id}' из категории '{category}' успешно получен.")
        else:
            logger.debug(f"TickCacheManager: Батч '{batch_id}' не найден в категории '{category}'.")

        return batch

    async def remove_batch_by_id(self, category: str, batch_id: str):
        """
        Удаляет конкретный батч по его ID из указанной категории.
        """
        current_batches_json_bytes = await self.redis.hget(REDIS_COORDINATOR_TASK_HASH, category)
        if not current_batches_json_bytes:
            logger.debug(f"TickCacheManager: Нечего удалять, категория '{category}' не найдена или пуста.")
            return

        current_batches = json.loads(current_batches_json_bytes.decode('utf-8'))
        if batch_id in current_batches:
            del current_batches[batch_id]
            if not current_batches:
                await self.redis.hdel(REDIS_COORDINATOR_TASK_HASH, category)
                logger.info(f"TickCacheManager: Категория '{category}' стала пустой и удалена из '{REDIS_COORDINATOR_TASK_HASH}'.")
            else:
                await self.redis.hset(REDIS_COORDINATOR_TASK_HASH, category, json.dumps(current_batches))
                logger.debug(f"TickCacheManager: Батч '{batch_id}' удален из категории '{category}'.")

            await self.redis.expire(REDIS_COORDINATOR_TASK_HASH, BATCH_TASK_TTL_SECONDS)
        else:
            logger.debug(f"TickCacheManager: Батч '{batch_id}' не найден в категории '{category}', ничего не удалено.")

    async def delete_all_categorized_tasks(self):
        """
        Удаляет весь хэш с категоризированными задачами из Redis.
        """
        await self.redis.delete(REDIS_COORDINATOR_TASK_HASH)
        logger.info(f"TickCacheManager: Хэш '{REDIS_COORDINATOR_TASK_HASH}' полностью удален.")

# Удаляем глобальный экземпляр
# tick_cache_manager: Optional['TickCacheManager'] = None