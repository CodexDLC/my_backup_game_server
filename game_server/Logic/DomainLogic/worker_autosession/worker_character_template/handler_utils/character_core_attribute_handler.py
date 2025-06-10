# Logic/DomainLogic/handlers_template/worker_character_template/handler_utils/character_core_attribute_handler.py

from typing import Dict, Any, List

# --- Существующие утилиты генерации атрибутов ---
from .character_stats_generator import generate_generated_base_stats
from .character_role_selector import assign_roles_and_archetypes_to_character_batch
from .character_skill_generator import distribute_initial_skill_levels


async def generate_core_attributes_for_single_character(
    quality_level: str
) -> Dict[str, Any]:
    """
    Генерирует основные атрибуты.
    Больше не принимает и не использует redis_client.
    """
    # Этап 1: Генерация 'base_stats'
    try:
        base_stats = generate_generated_base_stats(quality_level) 
    except Exception as e:
        raise ValueError(f"Ошибка генерации статов для quality_level {quality_level}") from e

    character_processing_data_list: List[Dict[str, Any]] = [{
        "quality_level": quality_level,
        "base_stats": base_stats
    }]

    # Этап 2: Назначение 'selected_role_name' и 'selected_archetype_name'
    try:
        batch_with_roles_archetypes = assign_roles_and_archetypes_to_character_batch(character_processing_data_list)
    except Exception as e:
        raise ValueError(f"Ошибка назначения роли/архетипа для quality_level {quality_level}") from e
        
    processed_single_char_data = batch_with_roles_archetypes[0] 
    initial_role_name = processed_single_char_data.get("selected_role_name", "UNASSIGNED_ROLE")
    selected_archetype_name = processed_single_char_data.get("selected_archetype_name", "UNASSIGNED_ARCHETYPE")

    # Этап 3: Распределение 'initial_skill_levels'
    try:
        # БЫЛО: await distribute_initial_skill_levels(batch_with_roles_archetypes, redis_client)
        # СТАЛО: Вызываем обновленную функцию без redis_client.
        batch_with_skills = await distribute_initial_skill_levels(batch_with_roles_archetypes)
        final_processed_char_data = batch_with_skills[0]
    except Exception as e:
        raise ValueError(f"Ошибка распределения навыков для quality_level {quality_level}, role {initial_role_name}") from e

    initial_skill_levels = final_processed_char_data.get("initial_skill_levels", {})

    result = {
        "base_stats": base_stats, 
        "initial_role_name": initial_role_name,
        "selected_archetype_name": selected_archetype_name, 
        "initial_skill_levels": initial_skill_levels
    }

    return result