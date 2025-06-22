# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_item/item_template_planner_logic.py

# -*- coding: utf-8 -*-
import json
import asyncio
import re
import time
import hashlib
import uuid
from typing import Dict, Any, Optional, List, Set, Tuple, Callable

# Главный импорт для всей конфигурации
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager
from game_server.config.provider import config

# Остальные импорты, не связанные с конфигами
from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.generator_utils import generate_item_code

# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager


# Обновленные импорты кэш-менеджеров (типизация)
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient # Для типизации
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import ITaskQueueCacheManager # Для типизации
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import IReferenceDataReader # Для типизации
from arq.connections import ArqRedis # Для типизации arq_redis_pool

# НЕ МЕНЯТЬ: from game_server.database.models.models import EquipmentTemplate # Оставить, если модель используется для типизации возвращаемых значений репозиторием
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches

# ДОБАВЛЕНО: Импорт ItemGenerationSpec DTO
from game_server.common_contracts.start_orcestrator.dtos import ItemGenerationSpec #


class ItemTemplatePlannerLogic:
    def __init__(
        self,
        repository_manager: RepositoryManager, # ИЗМЕНЕНО: теперь принимаем RepositoryManager
        central_redis_client: CentralRedisClient, # ИЗМЕНЕНО: точная типизация
        reference_data_reader: IReferenceDataReader, # ИЗМЕНЕНО: точная типизация
        task_queue_cache_manager: ITaskQueueCacheManager, # ИЗМЕНЕНО: точная типизация
        arq_redis_pool: ArqRedis, # ИЗМЕНЕНО: точная типизация
        item_generation_limit: Optional[int] = None
    ):
        # УДАЛЕНО: self.async_session_factory = async_session_factory
        self.repository_manager = repository_manager # ДОБАВЛЕНО: сохраняем RepositoryManager
        self.logger = logger
        self.central_redis_client = central_redis_client
        self.reference_data_reader = reference_data_reader
        self.task_queue_cache_manager = task_queue_cache_manager
        self.arq_redis_pool = arq_redis_pool # Этот атрибут больше не будет использоваться для enqueue_job здесь.
        
        self.redis_batch_store = RedisBatchStore(redis_client=self.central_redis_client) # RedisBatchStore принимает CentralRedisClient

        self.item_generation_limit = item_generation_limit
        logger.debug("✅ ItemTemplatePlannerLogic инициализирован.")

    async def _get_current_data_fingerprint(self) -> str:
        dependency_keys = [
            config.constants.redis.REDIS_KEY_GENERATOR_ITEM_BASE,
            config.constants.redis.REDIS_KEY_GENERATOR_MATERIALS,
            config.constants.redis.REDIS_KEY_GENERATOR_SUFFIXES,
        ]
        versions = await DataVersionManager.get_redis_fingerprint(self.central_redis_client, dependency_keys)
        fingerprint_str = json.dumps(versions, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()

    async def _get_cached_etalon_pool(self) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            async with self.central_redis_client.pipeline() as pipe:
                pipe.get(config.constants.redis.REDIS_KEY_ETALON_ITEM_POOL)
                pipe.get(config.constants.redis.REDIS_KEY_ETALON_ITEM_FINGERPRINT)
                results = await pipe.execute()
            
            pool_json, fingerprint_hash = results[0], results[1]
            if not pool_json or not fingerprint_hash:
                return None, None
            
            # ИЗМЕНЕНО: При загрузке из кэша, преобразуем словари обратно в ItemGenerationSpec объекты
            # Предполагаем, что в кэше они хранятся как словари (json.loads)
            cached_pool_dicts = json.loads(pool_json)
            cached_pool_specs = {k: ItemGenerationSpec(**v) for k, v in cached_pool_dicts.items()} # <--- ДОБАВЛЕНО
            
            return {k: spec.model_dump() for k, spec in cached_pool_specs.items()}, fingerprint_hash # Возвращаем словари, чтобы не менять сигнатуру метода get_or_build_etalon_specs пока что.
                                                                                                # В идеале, etalon_specs должны стать Dict[str, ItemGenerationSpec]
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке кэшированного эталонного пула: {e}", exc_info=True)
            return None, None

    async def _cache_etalon_pool(self, pool: Dict, fingerprint_hash: str):
        try:
            # ИЗМЕНЕНО: Убедимся, что pool содержит Pydantic объекты, и преобразуем их в словари для кэширования
            # pool_to_cache = {k: v.model_dump() if isinstance(v, ItemGenerationSpec) else v for k, v in pool.items()} # Если pool уже содержит ItemGenerationSpec
            pool_to_cache = pool # В текущей реализации pool уже Dict[str, Tuple], поэтому model_dump не нужен
                                 # Но если бы etalon_item_data_specs хранил ItemGenerationSpec, тогда бы pool_to_cache
                                 # был бы результатом преобразования этих объектов в dict.
            pool_json = json.dumps(pool_to_cache, ensure_ascii=False) # Используем pool_to_cache
            
            async with self.central_redis_client.pipeline() as pipe:
                pipe.set(config.constants.redis.REDIS_KEY_ETALON_ITEM_POOL, pool_json)
                pipe.set(config.constants.redis.REDIS_KEY_ETALON_ITEM_FINGERPRINT, fingerprint_hash)
                pipe.expire(config.constants.redis.REDIS_KEY_ETALON_ITEM_POOL, config.settings.prestart.ETALON_POOL_TTL_SECONDS)
                pipe.expire(config.constants.redis.REDIS_KEY_ETALON_ITEM_FINGERPRINT, config.settings.prestart.ETALON_POOL_TTL_SECONDS)
                await pipe.execute()
            self.logger.info(f"✅ Эталонный пул предметов успешно кэширован (хэш: {fingerprint_hash[:8]}...).")
        except Exception as e:
            self.logger.error(f"Ошибка при кэшировании эталонного пула: {e}", exc_info=True)

    # ИЗМЕНЕНО: Сигнатура метода теперь возвращает Dict[str, ItemGenerationSpec]
    async def get_or_build_etalon_specs(self) -> Dict[str, ItemGenerationSpec]:
        self.logger.debug("Проверка кэша для эталонного пула предметов...")
        
        current_fingerprint = await self._get_current_data_fingerprint()
        cached_pool_dicts, cached_fingerprint = await self._get_cached_etalon_pool() # cached_pool_dicts уже будут словарями

        if cached_pool_dicts is not None and current_fingerprint == cached_fingerprint:
            self.logger.debug(f"✅ Кэш эталонного пула актуален (хэш: {current_fingerprint[:8]}...). Используем кэшированную версию.")
            # ИЗМЕНЕНО: Преобразуем словари из кэша в ItemGenerationSpec объекты
            return {k: ItemGenerationSpec(**v) for k, v in cached_pool_dicts.items()} # <--- ДОБАВЛЕНО
        
        self.logger.warning(f"Кэш эталонного пула не найден или устарел. Запуск полного пересчета... (Текущий хэш: {current_fingerprint[:8]}, кэш: {cached_fingerprint[:8] if cached_fingerprint else 'N/A'})")
        
        item_base_raw, materials_raw, suffixes_raw, modifiers_raw = await self.load_reference_data_from_redis()
        
        item_base = item_base_raw if item_base_raw is not None else {}
        materials = materials_raw if materials_raw is not None else {}
        suffixes = suffixes_raw if suffixes_raw is not None else {}
        modifiers = modifiers_raw if modifiers_raw is not None else {}
        
        # ИЗМЕНЕНО: build_etalon_item_codes теперь возвращает Dict[str, ItemGenerationSpec]
        new_etalon_pool: Dict[str, ItemGenerationSpec] = self.build_etalon_item_codes(item_base, materials, suffixes)
        
        existing_codes_in_db = await self.get_existing_item_codes_from_db()
        new_etalon_item_codes = set(new_etalon_pool.keys())

        item_codes_to_delete = existing_codes_in_db - new_etalon_item_codes

        if item_codes_to_delete:
            deleted_count = await self._perform_item_deletions(list(item_codes_to_delete))
            self.logger.info(f"🗑️ Удалено {deleted_count} 'лишних' item_code из БД.")
        else:
            self.logger.debug("ℹ️ Нет 'лишних' item_code для удаления из БД.")

        # ИЗМЕНЕНО: Передаем словари для кэширования
        await self._cache_etalon_pool({k: v.model_dump() for k, v in new_etalon_pool.items()}, current_fingerprint) # <--- ДОБАВЛЕНО
        
        return new_etalon_pool

    async def load_reference_data_from_redis(self) -> tuple[Dict, Dict, Dict, Dict]:
        self.logger.debug("ItemTemplatePlannerLogic: Загрузка справочных данных из Redis через ReferenceDataReader...")
        item_base_result, materials_result, suffixes_result, modifiers_result = await asyncio.gather(
            self.reference_data_reader.get_all_item_bases(),
            self.reference_data_reader.get_all_materials(),
            self.reference_data_reader.get_all_suffixes(),
            self.reference_data_reader.get_all_modifiers()
        )
        
        item_base = item_base_result if item_base_result is not None else {}
        materials = materials_result if materials_result is not None else {}
        suffixes = suffixes_result if suffixes_result is not None else {}
        modifiers = modifiers_result if modifiers_result is not None else {}
        
        self.logger.debug(f"Загружено {len(item_base)} item_base, {len(materials)} материалов, {len(suffixes)} суффиксов, {len(modifiers)} модификаторов.")
        return item_base, materials, suffixes, modifiers

    async def get_existing_item_codes_from_db(self) -> Set[str]:
        repo = self.repository_manager.equipment_templates
        existing_codes = await repo.get_all_item_codes()
        self.logger.debug(f"ItemTemplatePlannerLogic: Получено {len(existing_codes)} существующих item_code из БД.")
        return set(existing_codes)

    async def _perform_item_deletions(self, item_codes_to_delete: List[str]) -> int:
        if not item_codes_to_delete:
            return 0
        
        try:
            repo = self.repository_manager.equipment_templates
            # Если delete_by_item_code_batch еще не реализован, нужно его добавить
            deleted_count = await repo.delete_by_item_code_batch(item_codes_to_delete)
            self.logger.info(f"🗑️ Успешно удалено {deleted_count} 'лишних' item_code из БД.")
            return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Ошибка при удалении item_code из БД: {e}", exc_info=True)
            return 0

    # ИЗМЕНЕНО: Сигнатура метода теперь возвращает Dict[str, ItemGenerationSpec]
    def build_etalon_item_codes(
        self, item_base_data: Dict[str, Any], materials_data: Dict[str, Any], suffixes_data: Dict[str, Any]
    ) -> Dict[str, ItemGenerationSpec]: # <--- ИЗМЕНЕНО
        etalon_item_data_specs: Dict[str, ItemGenerationSpec] = {} # <--- ИЗМЕНЕНО
        self.logger.info("ItemTemplatePlannerLogic: Начало формирования эталонного пула item_code.")
        start_time = time.time()

        if not item_base_data or not materials_data or not suffixes_data:
            self.logger.warning("Один или несколько наборов справочных данных пусты. Эталонный пул не будет построен.")
            return etalon_item_data_specs

        for base_code, base_info in item_base_data.items():
            category = base_info.get('category', 'UNKNOWN_CATEGORY')
            specific_names_map = base_info.get('names', {})
            if not specific_names_map: continue

            for original_specific_name, name_properties in specific_names_map.items():
                allowed_suffix_groups = set(name_properties.get('allowed_suffix_groups', []))

                for material_code, material_info in materials_data.items():
                    material_rarity_level = material_info.get('rarity_level')
                    rarity_level_to_use = config.constants.item.DEFAULT_RARITY_LEVEL if material_rarity_level is None else int(material_rarity_level)

                    material_type = material_info.get('type')
                    if not material_type: continue

                    category_rules = config.constants.item.MATERIAL_COMPATIBILITY_RULES.get(category, config.constants.item.MATERIAL_COMPATIBILITY_RULES["UNKNOWN_CATEGORY"])
                    if material_type in category_rules.get("disallowed_types", []) or material_type not in category_rules.get("allowed_types", []):
                        continue

                    for suffix_code, suffix_info in suffixes_data.items():
                        is_suffix_allowed = (suffix_code == "BASIC_EMPTY" or
                                             (suffix_info and suffix_info.get('group') and suffix_info.get('group') in allowed_suffix_groups))
                        if not is_suffix_allowed: continue

                        specific_name_for_code = re.sub(r'[^A-Z0-9]+', '-', original_specific_name).strip('-').upper()

                        item_code = generate_item_code(
                            category=category, base_code=base_code, specific_name=specific_name_for_code,
                            material_code=material_code, suffix_code=suffix_code, rarity_level=rarity_level_to_use
                        )

                        # ИЗМЕНЕНО: Создаем ItemGenerationSpec объект
                        spec_obj = ItemGenerationSpec(
                            item_code=item_code,
                            category=category,
                            base_code=base_code,
                            specific_name_key=original_specific_name,
                            material_code=material_code,
                            suffix_code=suffix_code,
                            rarity_level=rarity_level_to_use
                        )
                        etalon_item_data_specs[item_code] = spec_obj # <--- Теперь храним объект DTO

        elapsed_time = time.time() - start_time
        self.logger.info(f"ItemTemplatePlannerLogic: Построен эталонный пул из {len(etalon_item_data_specs)} уникальных item_code. Время выполнения: {elapsed_time:.2f} секунд.")
        return etalon_item_data_specs

    # ИЗМЕНЕНО: Сигнатура метода теперь принимает и возвращает List[ItemGenerationSpec]
    def find_missing_specs(self, etalon_specs: Dict[str, ItemGenerationSpec], existing_codes: Set[str]) -> List[ItemGenerationSpec]: # <--- ИЗМЕНЕНО
        return [spec for item_code, spec in etalon_specs.items() if item_code not in existing_codes]

    # ИЗМЕНЕНО: Сигнатура метода теперь принимает List[ItemGenerationSpec]
    async def prepare_tasks_for_missing_items(
        self, missing_specs: List[ItemGenerationSpec], item_generation_limit: Optional[int] # <--- ИЗМЕНЕНО
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Начало подготовки задач для {len(missing_specs)} недостающих предметов.")

        specs_to_process = missing_specs
        if item_generation_limit is not None and item_generation_limit >= 0:
            specs_to_process = missing_specs[:item_generation_limit]
            self.logger.debug(f"Применен лимит генерации: будет обработано {len(specs_to_process)} спецификаций.")

        if not specs_to_process:
            self.logger.info("Нет спецификаций для обработки после применения лимита. Возвращаем пустой список задач.")
            return []

        generated_task_entries = []

        # split_into_batches теперь будет получать List[ItemGenerationSpec]
        for batch_specs_objs in split_into_batches(specs_to_process, config.settings.prestart.ITEM_GENERATION_BATCH_SIZE): # <--- ИЗМЕНЕНО: переименовал переменную для ясности

            # ИЗМЕНЕНО: Преобразуем список ItemGenerationSpec объектов в список словарей для Redis/JSON
            batch_specs_as_dicts = [
                spec_obj.model_dump(by_alias=True) # ИСПОЛЬЗУЕМ Pydantic метод для преобразования в dict
                for spec_obj in batch_specs_objs # <--- ИЗМЕНЕНО: используем объекты ItemGenerationSpec
            ]

            redis_worker_batch_id = str(uuid.uuid4())
            
            self.logger.critical(f"*** DEBUG_ENQUEUE_ITEM_PRE: Batch ID='{redis_worker_batch_id}', Chunk Size={len(batch_specs_as_dicts)}")

            success = await self.task_queue_cache_manager.add_task_to_queue(
                batch_id=redis_worker_batch_id,
                key_template=config.constants.redis.ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                specs=batch_specs_as_dicts, # Здесь все еще ожидаются словари, так как это данные для Redis/ARQ
                target_count=len(batch_specs_as_dicts),
                initial_status="pending"
            )

            if success:
                generated_task_entries.append({"batch_id": redis_worker_batch_id})
                self.logger.info(f"Батч ID '{redis_worker_batch_id}' успешно подготовлен и сохранен в Redis. Ожидает постановки в ARQ.")
            else:
                self.logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' в Redis. ARQ-задача не будет отправлена.")

        self.logger.info(f"Подготовлено {len(generated_task_entries)} батчей задач на генерацию предметов. Готов к постановке в очередь ARQ.")
        return generated_task_entries