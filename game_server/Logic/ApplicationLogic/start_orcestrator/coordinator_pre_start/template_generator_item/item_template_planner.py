# game_server/Logic/ApplicationLogic/start_orcestrator/template_generator_item/item_template_planner.py

import json
import re
from typing import Any, Dict, List, Callable, Set, Optional, Tuple
# from sqlalchemy.ext.asyncio import AsyncSession # УДАЛЕНО: больше не нужна напрямую

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

from game_server.config.provider import config

from .item_template_planner_logic import ItemTemplatePlannerLogic

# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
# ДОБАВЛЕНО/ИЗМЕНЕНО: Импорты для более точной типизации зависимостей
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import IReferenceDataReader # Предполагаем интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import ITaskQueueCacheManager # Предполагаем интерфейс
from arq.connections import ArqRedis # Для arq_redis_pool

# ДОБАВЛЕНО: Импорт ItemGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import ItemGenerationSpec #

class ItemTemplatePlanner:
    def __init__(
        self,
        repository_manager: RepositoryManager, # ИЗМЕНЕНО: теперь принимаем RepositoryManager
        central_redis_client: CentralRedisClient, # ИЗМЕНЕНО: точная типизация
        reference_data_reader: IReferenceDataReader, # ИЗМЕНЕНО: точная типизация
        # 🔥 НОВОЕ: Теперь принимаем эти два аргумента
        task_queue_cache_manager: ITaskQueueCacheManager, # ИЗМЕНЕНО: точная типизация
        arq_redis_pool: ArqRedis, # ИЗМЕНЕНО: точная типизация
        item_generation_limit: Optional[int] = None
    ):
        # УДАЛЕНО: self.async_session_factory = async_session_factory
        self.repository_manager = repository_manager # ДОБАВЛЕНО: сохраняем RepositoryManager
        self.item_generation_limit = item_generation_limit

        self.planner_logic = ItemTemplatePlannerLogic(
            repository_manager=self.repository_manager, # ИЗМЕНЕНО: передаем RepositoryManager
            central_redis_client=central_redis_client,
            reference_data_reader=reference_data_reader,
            # 🔥 НОВОЕ: И передаем их в ItemTemplatePlannerLogic
            task_queue_cache_manager=task_queue_cache_manager,
            arq_redis_pool=arq_redis_pool,
            item_generation_limit=item_generation_limit
        )
        logger.debug("✨ ItemTemplatePlanner инициализирован.")

    async def check_and_prepare_generation_tasks(self) -> List[Dict[str, Any]]:
        logger.debug("ItemTemplatePlanner: Запуск check_and_prepare_generation_tasks (оркестратор)...")

        # ВНУТРИ planner_logic, методы get_or_build_etalon_specs и get_existing_item_codes_from_db
        # должны теперь использовать repository_manager, который им был передан.
        # ИЗМЕНЕНО: Типизация etalon_specs должна быть Dict[str, ItemGenerationSpec]
        etalon_specs: Dict[str, ItemGenerationSpec] = await self.planner_logic.get_or_build_etalon_specs() #
        existing_codes_in_db: Set[str] = await self.planner_logic.get_existing_item_codes_from_db()
        
        # ИЗМЕНЕНО: Типизация missing_specs должна быть List[ItemGenerationSpec]
        missing_specs: List[ItemGenerationSpec] = self.planner_logic.find_missing_specs(etalon_specs, existing_codes_in_db) #

        if missing_specs:
            logger.info(f"ItemTemplatePlanner: Найдено {len(missing_specs)} отсутствующих item_code. Подготовка задач для генерации.")
            # prepare_tasks_for_missing_items теперь принимает List[ItemGenerationSpec]
            tasks = await self.planner_logic.prepare_tasks_for_missing_items(
                missing_specs, self.item_generation_limit
            )
            logger.debug(f"ItemTemplatePlanner: Подготовлено {len(tasks)} задач генерации предметов.")
            return tasks
        else:
            logger.debug("ItemTemplatePlanner: Нет недостающих item_code для генерации. Все актуально.")
            return []