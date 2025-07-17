# game_server/Logic/ApplicationLogic/world_orchestrator/workers/item_generator/item_template_planner_logic.py

import json
import asyncio
import hashlib
import re
import uuid
import time
import logging
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository
from game_server.Logic.ApplicationLogic.world_orchestrator.start_orcestrator_utils.generator_utils import generate_item_code
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.arq_worker.utils.task_batch_dispatcher import split_into_batches


# Прямой импорт констант
from game_server.config.constants.arq import KEY_ITEM_GENERATION_TASK
from game_server.config.settings.process.prestart import ETALON_POOL_TTL_SECONDS
from game_server.config.constants.redis_key.reference_data_keys import (
    REDIS_KEY_GENERATOR_ITEM_BASE,
    REDIS_KEY_GENERATOR_MATERIALS,
    REDIS_KEY_GENERATOR_SUFFIXES,
)
from game_server.config.constants.redis import (
    REDIS_KEY_ETALON_ITEM_POOL,
    REDIS_KEY_ETALON_ITEM_FINGERPRINT,
)
from game_server.contracts.dtos.orchestrator.data_models import ItemGenerationSpec


# === Функции-помощники (ранее были приватными методами) ===

async def _get_current_data_fingerprint(central_redis_client: CentralRedisClient) -> str:
    dependency_keys = [
        REDIS_KEY_GENERATOR_ITEM_BASE,
        REDIS_KEY_GENERATOR_MATERIALS,
        REDIS_KEY_GENERATOR_SUFFIXES,
    ]
    versions = await DataVersionManager.get_redis_fingerprint(central_redis_client, dependency_keys)
    fingerprint_str = json.dumps(versions, sort_keys=True)
    return hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()

async def _get_cached_etalon_pool(central_redis_client: CentralRedisClient) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        async with central_redis_client.pipeline() as pipe:
            pipe.get(REDIS_KEY_ETALON_ITEM_POOL)
            pipe.get(REDIS_KEY_ETALON_ITEM_FINGERPRINT)
            results = await pipe.execute()
        pool_json, fingerprint_hash = results[0], results[1]
        if not pool_json or not fingerprint_hash:
            return None, None
        return json.loads(pool_json), fingerprint_hash
    except Exception:
        return None, None

async def _cache_etalon_pool(pool: Dict, fingerprint_hash: str, central_redis_client: CentralRedisClient, logger: logging.Logger):
    try:
        pool_json = json.dumps(pool, ensure_ascii=False)
        async with central_redis_client.pipeline() as pipe:
            pipe.set(REDIS_KEY_ETALON_ITEM_POOL, pool_json)
            pipe.set(REDIS_KEY_ETALON_ITEM_FINGERPRINT, fingerprint_hash)
            pipe.expire(REDIS_KEY_ETALON_ITEM_POOL, ETALON_POOL_TTL_SECONDS)
            pipe.expire(REDIS_KEY_ETALON_ITEM_FINGERPRINT, ETALON_POOL_TTL_SECONDS)
            await pipe.execute()
        logger.info(f"✅ Эталонный пул предметов успешно кэширован (хэш: {fingerprint_hash[:8]}...).")
    except Exception as e:
        logger.error(f"Ошибка при кэшировании эталонного пула: {e}", exc_info=True)


# === Основные функции логики ===

def build_etalon_item_codes(
    item_base_data: Dict[str, Any],
    materials_data: Dict[str, Any],
    suffixes_data: Dict[str, Any],
    default_rarity_level: int,
    material_compatibility_rules: dict,
    logger: logging.Logger,
) -> Dict[str, ItemGenerationSpec]:
    etalon_item_data_specs: Dict[str, ItemGenerationSpec] = {}
    logger.info("Logic: Начало формирования эталонного пула item_code.")
    start_time = time.time()

    if not item_base_data or not materials_data or not suffixes_data:
        logger.warning("Один или несколько наборов справочных данных пусты. Эталонный пул не будет построен.")
        return etalon_item_data_specs

    for base_code, base_info in item_base_data.items():
        category = base_info.get('category', 'UNKNOWN_CATEGORY')
        specific_names_map = base_info.get('names', {})
        if not specific_names_map: continue
        for original_specific_name, name_properties in specific_names_map.items():
            allowed_suffix_groups = set(name_properties.get('allowed_suffix_groups', []))
            for material_code, material_info in materials_data.items():
                material_rarity_level = material_info.get('rarity_level')
                rarity_level_to_use = default_rarity_level if material_rarity_level is None else int(material_rarity_level)
                material_type = material_info.get('type')
                if not material_type: continue
                category_rules = material_compatibility_rules.get(category, material_compatibility_rules.get("UNKNOWN_CATEGORY", {}))
                if material_type in category_rules.get("disallowed_types", []) or material_type not in category_rules.get("allowed_types", []):
                    continue
                for suffix_code, suffix_info in suffixes_data.items():
                    is_suffix_allowed = (suffix_code == "BASIC_EMPTY" or (suffix_info and suffix_info.get('group') and suffix_info.get('group') in allowed_suffix_groups))
                    if not is_suffix_allowed: continue
                    specific_name_for_code = re.sub(r'[^A-Z0-9]+', '-', original_specific_name).strip('-').upper()
                    item_code = generate_item_code(
                        category=category, base_code=base_code, specific_name=specific_name_for_code,
                        material_code=material_code, suffix_code=suffix_code, rarity_level=rarity_level_to_use
                    )
                    spec_obj = ItemGenerationSpec(
                        item_code=item_code, category=category, base_code=base_code,
                        specific_name_key=original_specific_name, material_code=material_code,
                        suffix_code=suffix_code, rarity_level=rarity_level_to_use
                    )
                    etalon_item_data_specs[item_code] = spec_obj

    elapsed_time = time.time() - start_time
    logger.info(f"Logic: Построен эталонный пул из {len(etalon_item_data_specs)} уникальных item_code. Время выполнения: {elapsed_time:.2f} секунд.")
    return etalon_item_data_specs


def find_missing_specs(etalon_specs: Dict[str, ItemGenerationSpec], existing_codes: Set[str]) -> List[ItemGenerationSpec]:
    return [spec for item_code, spec in etalon_specs.items() if item_code not in existing_codes]

async def prepare_tasks_for_missing_items(
    missing_specs: List[ItemGenerationSpec],
    item_generation_limit: Optional[int],
    item_generation_batch_size: int,
    batch_task_ttl: int,
    redis_batch_store: RedisBatchStore,
    logger: logging.Logger,
) -> List[Dict[str, Any]]:
    logger.debug(f"Начало подготовки задач для {len(missing_specs)} недостающих предметов.")
    specs_to_process = missing_specs
    if item_generation_limit is not None and item_generation_limit >= 0:
        specs_to_process = missing_specs[:item_generation_limit]
        logger.debug(f"Применен лимит генерации: будет обработано {len(specs_to_process)} спецификаций.")
    if not specs_to_process:
        return []
    generated_task_entries = []
    for batch_specs_objs in split_into_batches(specs_to_process, item_generation_batch_size):
        batch_specs_as_dicts = [spec_obj.model_dump(by_alias=True) for spec_obj in batch_specs_objs]
        redis_worker_batch_id = str(uuid.uuid4())
        batch_data_to_save = {"specs": batch_specs_as_dicts, "target_count": len(batch_specs_as_dicts), "status": "pending"}
        success = await redis_batch_store.save_batch(
            key_template=KEY_ITEM_GENERATION_TASK,
            batch_id=redis_worker_batch_id,
            batch_data=batch_data_to_save,
            ttl_seconds=batch_task_ttl
        )
        if success:
            generated_task_entries.append({"batch_id": redis_worker_batch_id})
            logger.info(f"Батч ID '{redis_worker_batch_id}' успешно подготовлен и сохранен в Redis.")
        else:
            logger.error(f"Не удалось сохранить батч ID '{redis_worker_batch_id}' в Redis.")
    logger.info(f"Подготовлено {len(generated_task_entries)} батчей задач на генерацию предметов.")
    return generated_task_entries