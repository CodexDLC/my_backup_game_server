# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_item/item_template_planner_logic.py
import json
import asyncio
import hashlib
import re
import uuid
import time
from typing import Dict, Any, Optional, List, Set, Tuple

from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager
from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.generator_utils import generate_item_code
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.ApplicationLogic.start_orcestrator.start_orcestrator_utils.batch_utils import split_into_batches
from game_server.common_contracts.dtos.orchestrator_dtos import ItemGenerationSpec
from game_server.config.settings.process.prestart import ETALON_POOL_TTL_SECONDS
from game_server.config.provider import config
from game_server.config.constants.redis_key.task_keys import KEY_ITEM_GENERATION_TASK

from game_server.config.constants.redis_key.reference_data_keys import (
    REDIS_KEY_GENERATOR_ITEM_BASE,
    REDIS_KEY_GENERATOR_MATERIALS,
    REDIS_KEY_GENERATOR_SUFFIXES,
   
)
from game_server.config.constants.redis import (
    REDIS_KEY_ETALON_ITEM_POOL, 
    REDIS_KEY_ETALON_ITEM_FINGERPRINT,   
)


class ItemTemplatePlannerLogic:
    def __init__(
        self,
        repository_manager: RepositoryManager,
        central_redis_client: CentralRedisClient,
        reference_data_reader: IReferenceDataReader,
        redis_batch_store: RedisBatchStore,
        item_generation_limit: Optional[int] = None
    ):
        self.repository_manager = repository_manager
        self.logger = logger
        self.central_redis_client = central_redis_client
        self.reference_data_reader = reference_data_reader
        self.redis_batch_store = redis_batch_store
        self.item_generation_limit = item_generation_limit
        logger.debug("✅ ItemTemplatePlannerLogic (v3) инициализирован.")

    async def _get_current_data_fingerprint(self) -> str:
        dependency_keys = [
            REDIS_KEY_GENERATOR_ITEM_BASE,
            REDIS_KEY_GENERATOR_MATERIALS,
            REDIS_KEY_GENERATOR_SUFFIXES,
        ]
        versions = await DataVersionManager.get_redis_fingerprint(self.central_redis_client, dependency_keys)
        fingerprint_str = json.dumps(versions, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()

    async def _get_cached_etalon_pool(self) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            async with self.central_redis_client.pipeline() as pipe:
                pipe.get(REDIS_KEY_ETALON_ITEM_POOL)
                pipe.get(REDIS_KEY_ETALON_ITEM_FINGERPRINT)
                results = await pipe.execute()
            
            pool_json, fingerprint_hash = results[0], results[1]
            if not pool_json or not fingerprint_hash:
                return None, None
            
            cached_pool_dicts = json.loads(pool_json)
            # Примечание: Преобразование в DTO теперь происходит в вызывающем методе get_or_build_etalon_specs
            return cached_pool_dicts, fingerprint_hash
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке кэшированного эталонного пула: {e}", exc_info=True)
            return None, None

    async def _cache_etalon_pool(self, pool: Dict, fingerprint_hash: str):
        try:
            # Убеждаемся, что на вход подаются словари
            pool_json = json.dumps(pool, ensure_ascii=False)
            
            async with self.central_redis_client.pipeline() as pipe:
                pipe.set(REDIS_KEY_ETALON_ITEM_POOL, pool_json)
                pipe.set(REDIS_KEY_ETALON_ITEM_FINGERPRINT, fingerprint_hash)
                pipe.expire(REDIS_KEY_ETALON_ITEM_POOL, ETALON_POOL_TTL_SECONDS)
                pipe.expire(REDIS_KEY_ETALON_ITEM_FINGERPRINT, ETALON_POOL_TTL_SECONDS)
                await pipe.execute()
            self.logger.info(f"✅ Эталонный пул предметов успешно кэширован (хэш: {fingerprint_hash[:8]}...).")
        except Exception as e:
            self.logger.error(f"Ошибка при кэшировании эталонного пула: {e}", exc_info=True)

    async def get_or_build_etalon_specs(self) -> Dict[str, ItemGenerationSpec]:
        self.logger.debug("Проверка кэша для эталонного пула предметов...")
        
        current_fingerprint = await self._get_current_data_fingerprint()
        cached_pool_dicts, cached_fingerprint = await self._get_cached_etalon_pool()

        if cached_pool_dicts is not None and current_fingerprint == cached_fingerprint:
            self.logger.debug(f"✅ Кэш эталонного пула актуален (хэш: {current_fingerprint[:8]}...). Используем кэшированную версию.")
            return {k: ItemGenerationSpec(**v) for k, v in cached_pool_dicts.items()}
        
        self.logger.warning(f"Кэш эталонного пула не найден или устарел. Запуск полного пересчета... (Текущий хэш: {current_fingerprint[:8]}, кэш: {cached_fingerprint[:8] if cached_fingerprint else 'N/A'})")
        
        item_base_raw, materials_raw, suffixes_raw, _ = await self.load_reference_data_from_redis()
        
        item_base = item_base_raw if item_base_raw is not None else {}
        materials = materials_raw if materials_raw is not None else {}
        suffixes = suffixes_raw if suffixes_raw is not None else {}
        
        new_etalon_pool = self.build_etalon_item_codes(item_base, materials, suffixes)
        
        existing_codes_in_db = await self.get_existing_item_codes_from_db()
        new_etalon_item_codes = set(new_etalon_pool.keys())

        item_codes_to_delete = existing_codes_in_db - new_etalon_item_codes

        if item_codes_to_delete:
            deleted_count = await self._perform_item_deletions(list(item_codes_to_delete))
            self.logger.info(f"🗑️ Удалено {deleted_count} 'лишних' item_code из БД.")
        else:
            self.logger.debug("ℹ️ Нет 'лишних' item_code для удаления из БД.")

        await self._cache_etalon_pool({k: v.model_dump() for k, v in new_etalon_pool.items()}, current_fingerprint)
        
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
            deleted_count = await repo.delete_by_item_code_batch(item_codes_to_delete)
            self.logger.info(f"🗑️ Успешно удалено {deleted_count} 'лишних' item_code из БД.")
            return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Ошибка при удалении item_code из БД: {e}", exc_info=True)
            return 0

    def build_etalon_item_codes(
        self, item_base_data: Dict[str, Any], materials_data: Dict[str, Any], suffixes_data: Dict[str, Any]
    ) -> Dict[str, ItemGenerationSpec]:
        etalon_item_data_specs: Dict[str, ItemGenerationSpec] = {}
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

                        spec_obj = ItemGenerationSpec(
                            item_code=item_code,
                            category=category,
                            base_code=base_code,
                            specific_name_key=original_specific_name,
                            material_code=material_code,
                            suffix_code=suffix_code,
                            rarity_level=rarity_level_to_use
                        )
                        etalon_item_data_specs[item_code] = spec_obj

        elapsed_time = time.time() - start_time
        self.logger.info(f"ItemTemplatePlannerLogic: Построен эталонный пул из {len(etalon_item_data_specs)} уникальных item_code. Время выполнения: {elapsed_time:.2f} секунд.")
        return etalon_item_data_specs

    def find_missing_specs(self, etalon_specs: Dict[str, ItemGenerationSpec], existing_codes: Set[str]) -> List[ItemGenerationSpec]:
        return [spec for item_code, spec in etalon_specs.items() if item_code not in existing_codes]

    async def prepare_tasks_for_missing_items(
        self, missing_specs: List[ItemGenerationSpec], item_generation_limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Начало подготовки задач для {len(missing_specs)} недостающих предметов.")

        specs_to_process = missing_specs
        if item_generation_limit is not None and item_generation_limit >= 0:
            specs_to_process = missing_specs[:item_generation_limit]
            self.logger.debug(f"Применен лимит генерации: будет обработано {len(specs_to_process)} спецификаций.")

        if not specs_to_process:
            return []

        generated_task_entries = []

        for batch_specs_objs in split_into_batches(specs_to_process, config.settings.prestart.ITEM_GENERATION_BATCH_SIZE):
            batch_specs_as_dicts = [spec_obj.model_dump(by_alias=True) for spec_obj in batch_specs_objs]
            redis_worker_batch_id = str(uuid.uuid4())
            
            batch_data_to_save = {
                "specs": batch_specs_as_dicts,
                "target_count": len(batch_specs_as_dicts),
                "status": "pending"
            }

            # <<< ИСПРАВЛЕНО: Добавлен обязательный аргумент 'key_template' в вызов метода
            success = await self.redis_batch_store.save_batch(
                key_template=KEY_ITEM_GENERATION_TASK, # <<< ВОТ ОН
                batch_id=redis_worker_batch_id,
                batch_data=batch_data_to_save,
                ttl_seconds=config.settings.redis.BATCH_TASK_TTL_SECONDS
            )

            if success:
                generated_task_entries.append({"batch_id": redis_worker_batch_id})
                self.logger.info(f"Батч ID '{redis_worker_batch_id}' успешно подготовлен и сохранен в Redis. Ожидает постановки в ARQ.")
            else:
                self.logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' в Redis. ARQ-задача не будет отправлена.")

        self.logger.info(f"Подготовлено {len(generated_task_entries)} батчей задач на генерацию предметов.")
        return generated_task_entries