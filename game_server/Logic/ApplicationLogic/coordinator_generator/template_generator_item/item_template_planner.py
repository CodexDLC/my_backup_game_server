# game_server/Logic/ApplicationLogic/coordinator_generator/template_generator_item/item_template_planner.py

import json
import re 
from typing import Any, Dict, List, Callable, Set, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.ApplicationLogic.coordinator_generator.generator_settings import ITEM_GENERATION_LIMIT
from game_server.services.logging.logging_setup import logger

# Импортируем сам КЛАСС ItemTemplatePlannerLogic
from .item_template_planner_logic import ItemTemplatePlannerLogic 
# 🔥 ИЗМЕНЕНИЕ: Этот импорт больше не нужен, так как мы не создаем клиент вручную
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient


class ItemTemplatePlanner:
    """
    Класс-планировщик (оркестратор). Отвечает за определение "ЧТО" нужно сгенерировать
    и координацию процесса, вызывая детальную логику.
    """
    def __init__(
        self,
        async_session_factory: Callable[[], AsyncSession],
        item_generation_limit: Optional[int] = ITEM_GENERATION_LIMIT
    ):
        self.async_session_factory = async_session_factory
        self.item_generation_limit = item_generation_limit
        # 🔥 ИСПРАВЛЕНИЕ: Инициализируем ItemTemplatePlannerLogic без лишних аргументов.
        # Теперь он сам знает, как получить доступ к данным через инкапсулированные менеджеры.
        self._planner_logic = ItemTemplatePlannerLogic(
            async_session_factory=self.async_session_factory,
            item_generation_limit=self.item_generation_limit
        )

    async def check_and_prepare_generation_tasks(self) -> List[Dict]:
        logger.info("ItemTemplatePlanner: Запуск check_and_prepare_generation_tasks (оркестратор)...")
        
        # Вызываем методы через экземпляр self._planner_logic
        item_base, materials, suffixes, modifiers = await self._planner_logic.load_reference_data_from_redis()
        
        existing_codes = await self._planner_logic.get_existing_item_codes_from_db()
        
        etalon_specs = self._planner_logic.build_etalon_item_codes(item_base, materials, suffixes)
        
        missing_specs = self._planner_logic.find_missing_specs(etalon_specs, existing_codes)
        
        tasks = self._planner_logic.prepare_tasks_for_missing_items(missing_specs, self.item_generation_limit)
        
        logger.info("ItemTemplatePlanner: Планирование задач завершено.")
        
        return tasks
