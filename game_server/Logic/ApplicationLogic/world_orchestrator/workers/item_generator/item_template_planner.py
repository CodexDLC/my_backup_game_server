# game_server/Logic/ApplicationLogic/world_orchestrator/workers/item_generator/item_template_planner.py

import asyncio
import logging
import inject
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем зависимости, которые нужны этому классу
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.config.constants.item import DEFAULT_RARITY_LEVEL, MATERIAL_COMPATIBILITY_RULES
from game_server.config.settings.process.prestart import ITEM_GENERATION_BATCH_SIZE, ITEM_GENERATION_LIMIT
from game_server.config.settings.redis_setting import BATCH_TASK_TTL_SECONDS

# Импортируем наш новый модуль с stateless-логикой
from . import item_template_planner_logic as item_logic

# Импортируем константы


from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

class ItemTemplatePlanner:
    """
    Класс-оркестратор. Получает зависимости, управляет процессом планирования предметов.
    """
    # 👇 ШАГ 3: УБИРАЕМ session_factory ИЗ ВНЕДРЕНИЯ ЗАВИСИМОСТЕЙ
    @inject.autoparams(
        'logger', 'equipment_template_repo_factory',
        'central_redis_client', 'reference_data_reader', 'redis_batch_store'
    )
    def __init__(
        self,
        logger: logging.Logger,
        equipment_template_repo_factory: Callable[[AsyncSession], IEquipmentTemplateRepository],
        central_redis_client: CentralRedisClient,
        reference_data_reader: IReferenceDataReader,
        redis_batch_store: RedisBatchStore
    ):
        self.logger = logger
        # self._session_factory больше не нужен
        self._equipment_template_repo_factory = equipment_template_repo_factory
        self._central_redis_client = central_redis_client
        self._reference_data_reader = reference_data_reader
        self._redis_batch_store = redis_batch_store
        
        # Сохраняем константы
        self.item_generation_limit = ITEM_GENERATION_LIMIT
        self.item_generation_batch_size = ITEM_GENERATION_BATCH_SIZE
        self.batch_task_ttl = BATCH_TASK_TTL_SECONDS
        self.default_rarity_level = DEFAULT_RARITY_LEVEL
        self.material_compatibility_rules = MATERIAL_COMPATIBILITY_RULES
        
        print(f"--- DEBUG: АТРИБУТ BATCH_TTL УСПЕШНО УСТАНОВЛЕН: {self.batch_task_ttl} ---")
        
    @transactional(AsyncSessionLocal)
    async def run_item_planning(self, session: AsyncSession):
        """
        Основной метод, запускающий всю цепочку планирования для предметов.
        """
        self.logger.info("➡️ ItemTemplatePlanner: Запуск планирования шаблонов ПРЕДМЕТОВ...")
        
        # 👇 ИЗМЕНЕНИЕ: Заменяем один неверный вызов на три правильных
        item_base_res, materials_res, suffixes_res = await asyncio.gather(
            self._reference_data_reader.get_all_item_bases(),
            self._reference_data_reader.get_all_materials(),
            self._reference_data_reader.get_all_suffixes()
        )
        
        # Проверяем на None, чтобы избежать ошибок
        item_base = item_base_res if item_base_res is not None else {}
        materials = materials_res if materials_res is not None else {}
        suffixes = suffixes_res if suffixes_res is not None else {}
        
        # 2. Строим эталонный пул
        etalon_pool = item_logic.build_etalon_item_codes(
            item_base_data=item_base, materials_data=materials, suffixes_data=suffixes,
            default_rarity_level=self.default_rarity_level,
            material_compatibility_rules=self.material_compatibility_rules,
            logger=self.logger
        )
        
        # 3. Получаем существующие коды из БД
        equipment_repo = self._equipment_template_repo_factory(session)
        existing_codes = await equipment_repo.get_all_item_codes()
        
        # 4. Находим, что нужно сгенерировать
        missing_specs = item_logic.find_missing_specs(etalon_pool, set(existing_codes))
        
        # 5. Готовим задачи для воркера
        item_tasks = await item_logic.prepare_tasks_for_missing_items(
            missing_specs=missing_specs,
            item_generation_limit=self.item_generation_limit,
            item_generation_batch_size=self.item_generation_batch_size,
            batch_task_ttl=self.batch_task_ttl,
            redis_batch_store=self._redis_batch_store,
            logger=self.logger
        )
        
        return item_tasks