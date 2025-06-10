# Logic/DomainLogic/handlers_template/worker_character_template/character_batch_processor.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# --- Логгер ---
from game_server.services.logging.logging_setup import logger

# --- Менеджеры и Хелперы ---
from game_server.Logic.DomainLogic.worker_autosession.generator_name.name_orchestrator import NameOrchestrator
from game_server.Logic.DomainLogic.worker_autosession.worker_character_template.handler_utils.redis_task_status_handler import get_task_specs_from_redis, set_task_final_status, update_task_generated_count
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.ORM_character_pool_manager import CharacterPoolRepository
# 🔥 ИЗМЕНЕНИЕ: Убираем ненужные импорты
# from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# from game_server.Logic.InfrastructureLogic.app_cache.services import task_queue_cache_manager

# --- Хендлеры из handler_utils ---
from .handler_utils.character_core_attribute_handler import generate_core_attributes_for_single_character
from .handler_utils.character_cache_handlers import (
    get_character_personality_id_from_cache,
    get_character_background_id_from_cache,     
    get_character_visual_data_placeholder
)
from .handler_utils.character_meta_handler import get_character_meta_attributes


# --- Основная функция-оркестратор обработки батча ---
async def process_character_batch_logic(
    redis_worker_batch_id: str,
    db_session: AsyncSession,
    task_key_template: str,
    target_quality_distribution: Dict[str, float],
    highest_quality_level_name: str
):
    """
    Оркестрирует полный процесс генерации персонажей для одного батча.
    """
    log_prefix = f"CHAR_BATCH_PROC_ID({redis_worker_batch_id}):"
    logger.info(f"{log_prefix} Начало обработки батча.")

    # 1. Получаем спецификации для генерации из Redis
    # 🔥 ИЗМЕНЕНИЕ: Вызов стал чистым, без лишних аргументов
    specifications, target_count, error = await get_task_specs_from_redis(
        batch_id=redis_worker_batch_id,
        task_key_template=task_key_template,
    )

    if error:
        logger.error(f"{log_prefix} Не удалось получить спецификации: {error}")
        # Статус 'failed' уже должен быть установлен внутри get_task_specs_from_redis
        return

    if not specifications:
        logger.info(f"{log_prefix} Батч не содержит спецификаций. Завершаем как пустой.")
        await set_task_final_status(
            redis_worker_batch_id, task_key_template, status="completed",
            final_generated_count=0, target_count=0, was_empty=True
        )
        return

    # 2. Инициализируем репозиторий для сохранения в БД
    char_pool_repo = CharacterPoolRepository(db_session)
    
    # 🔥 ИЗМЕНЕНИЕ: Локальный счетчик для сгенерированных персонажей
    generated_count = 0
    
    # 3. Последовательно генерируем каждого персонажа в батче
    for spec in specifications:
        try:
            # Извлекаем основные параметры из спецификации
            gender = spec.get("gender")
            quality_level = spec.get("quality_level")
            creature_type_id = spec.get("creature_type_id")

            if not all([gender, quality_level, creature_type_id]):
                logger.warning(f"{log_prefix} Пропущена неполная спецификация: {spec}")
                continue
            
            # --- Вызываем наши "чистые" хендлеры ---
            
            core_attributes = await generate_core_attributes_for_single_character(quality_level)
            first_name, last_name = NameOrchestrator.generate_character_name(gender=gender)
            personality_id = await get_character_personality_id_from_cache()
            background_story_id = await get_character_background_id_from_cache()
            meta_attributes = await get_character_meta_attributes(
                quality_level, highest_quality_level_name, target_quality_distribution
            )
            visual_appearance_data = await get_character_visual_data_placeholder()

            # --- Собираем полный словарь для записи в БД ---
            pool_entry_data = {
                "creature_type_id": creature_type_id,
                "gender": gender,
                "quality_level": quality_level,
                "base_stats": core_attributes.get("base_stats", {}),
                "initial_role_name": core_attributes.get("initial_role_name", "UNASSIGNED_ROLE"),
                "initial_skill_levels": core_attributes.get("initial_skill_levels", {}),
                "name": first_name,
                "surname": last_name,
                "personality_id": personality_id,
                "background_story_id": background_story_id,
                "visual_appearance_data": visual_appearance_data,
                "is_unique": meta_attributes.get("is_unique", False),
                "rarity_score": meta_attributes.get("rarity_score", 0),
                "status": "available",
            }
            
            # Сохраняем персонажа в БД
            await char_pool_repo.create(pool_entry_data)
            
            # Атомарно увеличиваем счетчик в Redis и обновляем локальный счетчик
            new_count = await update_task_generated_count(redis_worker_batch_id, task_key_template)
            if new_count is not None:
                generated_count = new_count

        except Exception as e:
            logger.error(f"{log_prefix} Ошибка при генерации одного персонажа: {e}", exc_info=True)
            # Пропускаем только эту спецификацию, но продолжаем обработку батча
            continue

    # 4. Финальное обновление статуса всего батча
    # 🔥 ИЗМЕНЕНИЕ: Используем наш локальный счетчик вместо несуществующего метода
    final_generated_count = generated_count
    
    await set_task_final_status(
        redis_worker_batch_id, task_key_template, status="completed",
        final_generated_count=final_generated_count, target_count=target_count
    )
    
    logger.info(f"{log_prefix} Обработка батча завершена. Сгенерировано: {final_generated_count}/{target_count}.")

