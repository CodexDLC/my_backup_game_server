import random
from typing import Dict, List, Any, Tuple, Optional, Set, Union
from collections import defaultdict, Counter

# --- Логгер ---
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# --- Константы ---
from game_server.config.provider import config

# НОВЫЙ ИМПОРТ: Для типизации ReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader # Уточненный импорт

# ДОБАВЛЕНО: Импорт SkillData DTO
from game_server.common_contracts.start_orcestrator.dtos import SkillData #


# 🔥 ИЗМЕНЕНИЕ: Функция теперь принимает skills_data как Dict[str, SkillData]
def _get_skill_categories_and_tags_from_config(skill_id: str, skills_data: Dict[str, SkillData]) -> Tuple[Set[str], Set[str]]: # <--- ИЗМЕНЕНО
    """Извлекает категории и теги навыка из переданных данных о навыках (SkillData DTO)."""
    skill_dto = skills_data.get(skill_id)
    if skill_dto:
        categories = set(skill_dto.categories) # Доступ к атрибуту DTO
        tags = set(skill_dto.tags) # Доступ к атрибуту DTO
        return categories, tags
    logger.warning(f"Навык с ID '{skill_id}' не найден в данных о навыках. Возвращаем пустые категории/теги.")
    return set(), set()


async def distribute_initial_skill_levels(
    character_data_batch: List[Dict[str, Any]], # Пока остается List[Dict[str, Any]]
    reference_data_reader: ReferenceDataReader,
) -> List[Dict[str, Any]]: # Пока остается List[Dict[str, Any]]
    """
    Распределяет начальные уровни навыков для батча персонажей.
    """
    if not character_data_batch:
        return []

    # ИЗМЕНЕНО: GAME_SKILLS_FROM_REDIS теперь будет Dict[str, SkillData]
    GAME_SKILLS_FROM_REDIS: Dict[str, SkillData] = await reference_data_reader.get_all_skills() # <--- ИЗМЕНЕНО

    if not GAME_SKILLS_FROM_REDIS:
        logger.warning("Нет данных о навыках из Redis. Навыки не будут распределены.")
        return character_data_batch

    updated_batch = []

    for char_data in character_data_batch:
        quality_level = char_data.get("quality_level")
        initial_role_name = char_data.get("selected_role_name", "UNASSIGNED_ROLE")

        quality_config = config.settings.character.CHARACTER_TEMPLATE_QUALITY_CONFIG.get(quality_level)
        if not quality_config:
            logger.error(f"Не найдена конфигурация качества для {quality_level}.")
            char_data["initial_skill_levels"] = {}
            updated_batch.append(char_data)
            continue

        max_total_skill_points = quality_config["max_total_skill_points"]
        max_skill_level_per_skill = quality_config["max_skill_level_per_skill"]
        min_active_skills = quality_config["min_active_skills"]
        max_active_skills = quality_config["max_active_skills"]

        role_config = config.constants.character.NPC_ROLES.get(initial_role_name)
        if not role_config:
            logger.warning(f"Не найдена конфигурация роли для {initial_role_name}. Навыки будут распределены без учета роли.")
            role_skill_preference_tags = set()
            role_specific_skills = set()
            role_limit_groups = []
        else:
            role_skill_preference_tags = set(role_config.get("skill_preference_tags", []))
            role_specific_skills = set(role_config.get("specific_skills", []))
            role_limit_groups = role_config.get("skill_preference_tags", {}).get("limit_groups", []) # Здесь опечатка, должно быть role_config.get("skill_limit_groups", [])

        initial_skill_levels: Dict[str, int] = {}
        assigned_skill_points = 0
        assigned_skill_count = 0
        assigned_skill_groups: Dict[str, int] = defaultdict(int)

        # available_skills_for_assignment теперь будет Dict[str, SkillData]
        available_skills_for_assignment = GAME_SKILLS_FROM_REDIS # <--- ИЗМЕНЕНО

        # Шаг 1: Приоритет - специфичные навыки роли
        for skill_id in role_specific_skills:
            if assigned_skill_points >= max_total_skill_points or assigned_skill_count >= max_active_skills:
                break
            # Проверяем, что skill_id действительно есть в GAME_SKILLS_FROM_REDIS
            if skill_id in available_skills_for_assignment and initial_skill_levels.get(skill_id, 0) < max_skill_level_per_skill:
                # ИЗМЕНЕНО: Передаем GAME_SKILLS_FROM_REDIS (теперь Dict[str, SkillData])
                skill_categories, skill_tags = _get_skill_categories_and_tags_from_config(skill_id, GAME_SKILLS_FROM_REDIS)
                can_assign = True
                for group in skill_categories:
                    limit_config = config.constants.character.SKILL_GROUP_LIMITS.get(group)
                    if limit_config and limit_config['limit_type'] == 'exclusive' and assigned_skill_groups[group] > 0:
                        can_assign = False
                        break
                
                if can_assign:
                    initial_skill_levels[skill_id] = initial_skill_levels.get(skill_id, 0) + 1
                    assigned_skill_points += 1
                    assigned_skill_count += 1
                    for group in skill_categories:
                        assigned_skill_groups[group] += 1

        # Шаг 2: Распределение оставшихся очков по предпочтительным навыкам и их тегам
        shuffled_available_skills = list(available_skills_for_assignment.keys())
        random.shuffle(shuffled_available_skills)

        for skill_id in shuffled_available_skills:
            if assigned_skill_points >= max_total_skill_points or assigned_skill_count >= max_active_skills:
                break
            
            # ИЗМЕНЕНО: Передаем GAME_SKILLS_FROM_REDIS (теперь Dict[str, SkillData])
            skill_categories, skill_tags = _get_skill_categories_and_tags_from_config(skill_id, GAME_SKILLS_FROM_REDIS)
            
            if not (role_skill_preference_tags.intersection(skill_tags) or skill_id in role_specific_skills):
                continue

            can_assign = True
            for group in skill_categories:
                limit_config = config.constants.character.SKILL_GROUP_LIMITS.get(group)
                if limit_config and limit_config['limit_type'] == 'exclusive' and assigned_skill_groups[group] > 0:
                    can_assign = False
                    break
            
            if can_assign and initial_skill_levels.get(skill_id, 0) < max_skill_level_per_skill:
                initial_skill_levels[skill_id] = initial_skill_levels.get(skill_id, 0) + 1
                assigned_skill_points += 1
                assigned_skill_count += 1
                for group in skill_categories:
                    assigned_skill_groups[group] += 1

        # Шаг 3: Гарантируем минимальное количество активных навыков
        while assigned_skill_count < min_active_skills and assigned_skill_points < max_total_skill_points:
            potential_skills = [
                s_id for s_id in GAME_SKILLS_FROM_REDIS.keys()
                if initial_skill_levels.get(s_id, 0) < max_skill_level_per_skill
            ]
            if not potential_skills:
                break
            
            skill_to_boost = random.choice(potential_skills)
            # ИЗМЕНЕНО: Передаем GAME_SKILLS_FROM_REDIS (теперь Dict[str, SkillData])
            skill_categories, _ = _get_skill_categories_and_tags_from_config(skill_to_boost, GAME_SKILLS_FROM_REDIS)
            
            can_assign = True
            for group in skill_categories:
                limit_config = config.constants.character.SKILL_GROUP_LIMITS.get(group)
                if limit_config and limit_config['limit_type'] == 'exclusive' and assigned_skill_groups[group] > 0:
                    can_assign = False
                    break
            
            if can_assign:
                initial_skill_levels[skill_to_boost] = initial_skill_levels.get(skill_to_boost, 0) + 1
                assigned_skill_points += 1
                assigned_skill_count += 1
                for group in skill_categories:
                    assigned_skill_groups[group] += 1

        char_data["initial_skill_levels"] = initial_skill_levels
        updated_batch.append(char_data)

    return updated_batch