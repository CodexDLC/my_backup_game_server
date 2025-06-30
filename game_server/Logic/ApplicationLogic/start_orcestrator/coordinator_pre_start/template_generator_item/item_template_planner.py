# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_item/item_template_planner.py

from typing import Any, Dict, List, Optional, Set

from game_server.config.logging.logging_setup import app_logger as logger
from .item_template_planner_logic import ItemTemplatePlannerLogic
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.common_contracts.dtos.orchestrator_dtos import ItemGenerationSpec

# 🔥 ИЗМЕНЕНИЕ: Импортируем RedisBatchStore, так как он теперь наша зависимость
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore


class ItemTemplatePlanner:
    """
    Класс-фасад, который оркестрирует логику планирования генерации предметов.
    Инициализирует и использует ItemTemplatePlannerLogic для выполнения основной работы.
    """
    def __init__(
        self,
        repository_manager: RepositoryManager,
        central_redis_client: CentralRedisClient,
        reference_data_reader: IReferenceDataReader,
        # 🔥 ИЗМЕНЕНИЕ: Заменяем старые зависимости на новую, правильную
        redis_batch_store: RedisBatchStore,
        item_generation_limit: Optional[int] = None
    ):
        self.repository_manager = repository_manager
        self.item_generation_limit = item_generation_limit

        # 🔥 ИЗМЕНЕНИЕ: Создаем ItemTemplatePlannerLogic с правильной зависимостью
        self.planner_logic = ItemTemplatePlannerLogic(
            repository_manager=self.repository_manager,
            central_redis_client=central_redis_client,
            reference_data_reader=reference_data_reader,
            redis_batch_store=redis_batch_store, # <--- Передаем правильную зависимость
            item_generation_limit=item_generation_limit
        )
        logger.debug("✨ ItemTemplatePlanner (v2) инициализирован.")

    async def check_and_prepare_generation_tasks(self) -> List[Dict[str, Any]]:
        """
        Главный метод, запускающий полный цикл проверки и подготовки задач.
        Делегирует выполнение в planner_logic.
        """
        logger.debug("ItemTemplatePlanner: Запуск check_and_prepare_generation_tasks...")

        etalon_specs: Dict[str, ItemGenerationSpec] = await self.planner_logic.get_or_build_etalon_specs()
        existing_codes_in_db: Set[str] = await self.planner_logic.get_existing_item_codes_from_db()
        
        missing_specs: List[ItemGenerationSpec] = self.planner_logic.find_missing_specs(etalon_specs, existing_codes_in_db)

        if missing_specs:
            logger.info(f"ItemTemplatePlanner: Найдено {len(missing_specs)} отсутствующих item_code. Подготовка задач для генерации.")
            tasks = await self.planner_logic.prepare_tasks_for_missing_items(
                missing_specs, self.item_generation_limit
            )
            logger.debug(f"ItemTemplatePlanner: Подготовлено {len(tasks)} задач генерации предметов.")
            return tasks
        else:
            logger.debug("ItemTemplatePlanner: Нет недостающих item_code для генерации. Все актуально.")
            return []
