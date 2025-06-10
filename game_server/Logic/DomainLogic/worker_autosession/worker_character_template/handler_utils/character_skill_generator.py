# game_server/Logic/DomainLogic/handlers_template/worker_character_template/handler_utils/character_skill_generator.py

import random
import json
from typing import Dict, List, Any

# --- КОНСТАНТЫ И ЛОГГЕР ---
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_character import CHARACTER_TEMPLATE_QUALITY_CONFIG, NPC_ARCHETYPES, NPC_ROLES, SKILL_GROUP_LIMITS
# 🔥 ИЗМЕНЕНИЕ: Исправляем импорт, чтобы получить КОНКРЕТНЫЙ ЭКЗЕМПЛЯР ридера
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data_reader import reference_data_reader
from game_server.services.logging.logging_setup import logger


# --- Вспомогательные функции (без изменений) ---

def _skill_matches_archetype(skill_definition: Dict[str, Any], archetype_data: Dict[str, Any]) -> bool:
    """Проверяет, соответствует ли навык предпочтениям архетипа."""
    if not archetype_data:
        return False
    archetype_pref_tags = archetype_data.get("skill_preference_tags", [])
    skill_category_tag = skill_definition.get("category_tag", "")
    skill_role_pref_tag = skill_definition.get("role_preference_tag", "")
    if skill_category_tag and skill_category_tag in archetype_pref_tags:
        return True
    if skill_role_pref_tag and skill_role_pref_tag in archetype_pref_tags:
        return True
    return False

def _calculate_skill_priority_score(
    skill_key: str, skill_definition: Dict[str, Any], role_data: Dict[str, Any],
    archetype_data: Dict[str, Any], character_base_stats: Dict[str, int]
) -> float:
    """Рассчитывает приоритетный скор для навыка."""
    score = 1.0
    role_preferences = role_data.get("skill_preference_tags", {})
    role_specific_skills = role_preferences.get("specific_skills", [])
    if skill_key in role_specific_skills:
        score += 100
    if _skill_matches_archetype(skill_definition, archetype_data):
        score += 50
    stat_influence = skill_definition.get("stat_influence", {})
    for stat_name, weight in stat_influence.items():
        score += character_base_stats.get(stat_name, 0) * weight
    return max(1.0, score)


# --- Основная функция с рефакторингом ---

async def distribute_initial_skill_levels(
    characters_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Распределяет начальные уровни навыков для каждого персонажа в батче,
    используя reference_data_reader для получения данных о навыках.
    """
    if not isinstance(characters_data, list):
        raise TypeError("characters_data должна быть списком словарей.")
    
    # Теперь этот вызов будет работать, так как мы импортировали правильный объект
    GAME_SKILLS_FROM_REDIS = await reference_data_reader.get_all_skills()
    
    if not GAME_SKILLS_FROM_REDIS:
        logger.warning("SKILL_GEN: Не удалось загрузить навыки из Redis. Возвращаем пустые навыки.")
        for char_data in characters_data:
            char_data["initial_skill_levels"] = {}
        return characters_data
    
    # --- Основная логика (без изменений) ---
    processed_characters: List[Dict[str, Any]] = []
    for char_data in characters_data:
        current_char_data = char_data.copy()
        required_keys = ["selected_role_name", "selected_archetype_name", "quality_level", "base_stats"]
        if not all(key in current_char_data for key in required_keys):
            missing_keys = [key for key in required_keys if key not in current_char_data]
            logger.warning(f"SKILL_GEN: Пропущен элемент из-за отсутствия ключей: {missing_keys}.")
            processed_characters.append(current_char_data)
            continue

        role_name = current_char_data["selected_role_name"]
        archetype_name = current_char_data["selected_archetype_name"]
        quality_level = current_char_data["quality_level"]
        base_stats = current_char_data["base_stats"]

        quality_config = CHARACTER_TEMPLATE_QUALITY_CONFIG.get(quality_level)
        role_data = NPC_ROLES.get(role_name, {})
        archetype_data = NPC_ARCHETYPES.get(archetype_name, {})

        if not quality_config:
            logger.warning(f"SKILL_GEN: Конфигурация качества '{quality_level}' не найдена. Пропускаем.")
            processed_characters.append(current_char_data)
            continue

        max_total_skill_points = quality_config.get("max_total_skill_points", 0)
        max_skill_level_cap = quality_config.get("max_skill_level_per_skill", 1)
        min_active_skills = quality_config.get("min_active_skills", 0)
        max_active_skills = quality_config.get("max_active_skills", len(GAME_SKILLS_FROM_REDIS))
        target_active_skills = min(random.randint(min_active_skills, max_active_skills), len(GAME_SKILLS_FROM_REDIS))

        skill_priority_scores = {
            skill_key: _calculate_skill_priority_score(skill_key, skill_def, role_data, archetype_data, base_stats)
            for skill_key, skill_def in GAME_SKILLS_FROM_REDIS.items()
        }
        
        sorted_potential_skills = sorted(
            GAME_SKILLS_FROM_REDIS.items(),
            key=lambda item: (skill_priority_scores.get(item[0], 0), item[1].get("rarity_weight", 0)),
            reverse=True
        )

        # Логика выбора активных скиллов, адаптированная из предыдущей версии
        activated_skill_keys = []
        skill_groups_count = {group: 0 for group in SKILL_GROUP_LIMITS}

        for skill_key, skill_def in sorted_potential_skills:
            if len(activated_skill_keys) >= target_active_skills:
                break
            
            group = skill_def.get("group")
            if group and group in skill_groups_count:
                if skill_groups_count[group] < SKILL_GROUP_LIMITS[group]:
                    activated_skill_keys.append(skill_key)
                    skill_groups_count[group] += 1
            else: # Для навыков без группы или для групп без лимита
                activated_skill_keys.append(skill_key)
        
        initial_skill_levels = {skill_name: 0 for skill_name in GAME_SKILLS_FROM_REDIS.keys()}
        for key in activated_skill_keys:
            initial_skill_levels[key] = 1 # Начальный уровень 1
        
        remaining_points = max_total_skill_points - len(activated_skill_keys)
        
        levelable_skills = [sk for sk in activated_skill_keys if initial_skill_levels[sk] < max_skill_level_cap]
        while remaining_points > 0 and levelable_skills:
            skill_to_level_up = random.choice(levelable_skills)
            initial_skill_levels[skill_to_level_up] += 1
            remaining_points -= 1
            if initial_skill_levels[skill_to_level_up] >= max_skill_level_cap:
                levelable_skills.remove(skill_to_level_up)

        current_char_data["initial_skill_levels"] = initial_skill_levels
        processed_characters.append(current_char_data)

    return processed_characters
