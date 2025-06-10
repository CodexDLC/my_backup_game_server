# coordinator_tick/coordinator/tick_task_processor.py

import uuid
from typing import Dict, List, Any

from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger

# Импортируем наш новый высокоуровневый менеджер кэша для тиков
from game_server.Logic.InfrastructureLogic.app_cache.services.tick_cache_manager import tick_cache_manager

# Импортируем константу размера батча
from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import BATCH_SIZE


from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient


class TaskProcessor:
    """
    Обработчик задач. Принимает сырой список персонажей по категориям,
    создает заглушки-инструкции, батчит их и сохраняет в Redis.
    Его роль - ТОЛЬКО подготовка батчей инструкций в Redis и возвращение их ID.
    Не вызывает методы координатора напрямую.
    """

    def __init__(self, redis=None, tick_cache_manager_instance=tick_cache_manager):
        """
        Инициализация TaskProcessor.
        :param redis: Существующее подключение к Redis (опционально).
        :param tick_cache_manager_instance: Экземпляр TickCacheManager.
        """
        self.redis = redis or CentralRedisClient()
        self._using_external_redis = redis is not None
        self.tick_cache_manager = tick_cache_manager_instance
        self._raw_tasks_by_category = {}

    async def prepare_and_process_batches(self, raw_tasks_by_category: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, str]]: # Изменено возвращаемое значение на List[Dict[str, str]]
        """
        Основной цикл обработки сырых задач.
        Принимает словарь с сырыми задачами, сгруппированными по категории.
        Создает батчи инструкций и сохраняет их в Redis.
        Возвращает список словарей, каждый из которых содержит {'batch_id': str, 'category': str}.

        :param raw_tasks_by_category: Словарь, где ключ - это категория (str),
                                       а значение - список словарей с задачами.
                                       Пример: {'exploration': [{'character_id': 101, 'task_type': 'exploration', ...}]}
        :return: Список словарей {'batch_id': str, 'category': str} созданных батчей.
        """
        self._raw_tasks_by_category = raw_tasks_by_category
        
        all_created_batch_info: List[Dict[str, str]] = [] # Изменено на список словарей

        try:
            logger.info("🚀 [START] TaskProcessor запущен для обработки сырых задач...")

            total_raw_tasks = sum(len(v) for v in self._raw_tasks_by_category.values())
            if total_raw_tasks > 0:
                logger.info(f"✅ Получено {total_raw_tasks} сырых задач по категориям: {list(self._raw_tasks_by_category.keys())}")
                all_created_batch_info = await self._collect_instructions_and_batch()
            else:
                logger.info("💤 Нет сырых задач для обработки, завершаем работу TaskProcessor.")

        except Exception as e:
            logger.error(f"❌ Ошибка в TaskProcessor: {str(e)}")
            all_created_batch_info = []
        finally:
            await self._cleanup_resources()
        
        return all_created_batch_info


    async def _collect_instructions_and_batch(self) -> List[Dict[str, str]]: # Изменено возвращаемое значение
        """
        Собирает инструкции для каждого character_id, формирует батчи
        и сохраняет их в Redis через TickCacheManager.
        Возвращает список словарей {'batch_id': str, 'category': str} всех созданных батчей.
        """
        logger.info("Начинаем сбор инструкций и формирование батчей...")

        all_instructions: Dict[str, List[Dict[str, Any]]] = {
            "exploration": [],
            "training": [],
            "crafting": []
        }
        created_batch_info: List[Dict[str, str]] = [] # Изменено на список словарей

        # --- ЗАГЛУШКА: Формирование инструкций ---
        for task_type, raw_tasks in self._raw_tasks_by_category.items():
            for task_data in raw_tasks:
                character_id = task_data.get('character_id')
                if character_id is None:
                    logger.warning(f"Сырая задача без 'character_id' пропущена: {task_data}")
                    continue
                
                instruction = {
                    "character_id": character_id,
                    "task_type": task_type,
                    "instruction_details": f"Process_tick_for_{task_type}_char_{character_id}",
                    **task_data 
                }
                
                if task_type in all_instructions:
                    all_instructions[task_type].append(instruction)
                else:
                    logger.warning(f"Неизвестный тип задачи '{task_type}' для батчинга. Инструкция пропущена.")
        # --- КОНЕЦ ЗАГЛУШКИ ---

        # --- БАТЧИНГ И СОХРАНЕНИЕ В REDIS ---
        batches_created = 0
        for category, instructions in all_instructions.items():
            if not instructions:
                continue

            for i in range(0, len(instructions), BATCH_SIZE):
                batch_content = instructions[i:i + BATCH_SIZE]
                batch_id = str(uuid.uuid4())
                
                await self.tick_cache_manager.add_batch_of_instructions_to_category(
                    category=category,
                    batch_id=batch_id,
                    instructions_batch=batch_content
                )
                created_batch_info.append({'batch_id': batch_id, 'category': category}) # Добавляем словарь
                batches_created += 1
                logger.info(f"Создан и сохранен батч '{batch_id}' ({len(batch_content)} инструкций) для категории '{category}'.")

        if batches_created > 0:
            logger.info(f"🏁 Завершено формирование и сохранение {batches_created} батчей инструкций в Redis.")
        else:
            logger.info("❌ Не было сформировано ни одного батча инструкций.")
        
        return created_batch_info # Возвращаем список словарей

    async def _cleanup_resources(self):
        """Очистка ресурсов."""
        if not self._using_external_redis:
            await self.redis.close()