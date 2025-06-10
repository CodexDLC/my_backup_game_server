# game_server/Logic/InfrastructureLogic/app_cache/services/tick_cache_manager.py

import logging
import json
from typing import Any, Dict, List, Optional

# Импортируем низкоуровневый клиент Redis
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client

# Импортируем константы TTL, определенные для тиков
from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import (
    BATCH_TASK_TTL_SECONDS
)

logger = logging.getLogger(__name__)

# Константы для ключей Redis, специфичные для тиковой системы
REDIS_COORDINATOR_TASK_HASH = "coordinator:tasks" 
REDIS_TASK_QUEUE_EXPLORATION = "exploration" 
REDIS_TASK_QUEUE_TRAINING = "training"     
REDIS_TASK_QUEUE_CRAFTING = "crafting"     


class TickCacheManager:
    """
    Высокоуровневый менеджер для кэширования и управления задачами тиковой системы в Redis.
    """
    # 🔥 ИЗМЕНЕНИЕ: Упрощаем __init__, как и в других менеджерах.
    def __init__(self):
        self.redis = central_redis_client
        logger.info("✅ TickCacheManager инициализирован.")

    # Все остальные методы остаются БЕЗ ИЗМЕНЕНИЙ,
    # так как они уже правильно используют self.redis.

    async def add_batch_of_instructions_to_category(self, category: str, batch_id: str, instructions_batch: List[Dict[str, Any]]):
        """
        Добавляет батч инструкций под уникальным ID в соответствующее поле категории
        в главном хэше REDIS_COORDINATOR_TASK_HASH.
        """
        if category not in [REDIS_TASK_QUEUE_EXPLORATION, REDIS_TASK_QUEUE_TRAINING, REDIS_TASK_QUEUE_CRAFTING]:
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
        for category, batches_json in all_categories_raw.items():
            try:
                batches_for_category = json.loads(batches_json)
                
                if isinstance(batches_for_category, dict):
                    categorized_batches[category] = batches_for_category
                    logger.debug(f"TickCacheManager: Извлечено {len(batches_for_category)} батчей для категории '{category}'.")
                else:
                    logger.error(f"TickCacheManager: Неожиданный формат данных для категории '{category}'.")

            except json.JSONDecodeError as e:
                logger.error(f"TickCacheManager: Ошибка десериализации данных для категории '{category}': {e}")

        logger.info(f"TickCacheManager: Завершено извлечение батчей из Redis. Всего категорий с батчами: {len(categorized_batches)}.")
        return categorized_batches

    async def get_batch_by_id(self, category: str, batch_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получает конкретный батч инструкций по его ID из указанной категории.
        """
        current_batches_json = await self.redis.hget(REDIS_COORDINATOR_TASK_HASH, category)
        if not current_batches_json:
            logger.debug(f"TickCacheManager: Категория '{category}' не найдена или пуста.")
            return None
        
        current_batches = json.loads(current_batches_json)
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
        current_batches_json = await self.redis.hget(REDIS_COORDINATOR_TASK_HASH, category)
        if not current_batches_json:
            logger.debug(f"TickCacheManager: Нечего удалять, категория '{category}' не найдена или пуста.")
            return
        
        current_batches = json.loads(current_batches_json)
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

# Создаем единственный экземпляр менеджера для использования в Backend'е
tick_cache_manager = TickCacheManager()
