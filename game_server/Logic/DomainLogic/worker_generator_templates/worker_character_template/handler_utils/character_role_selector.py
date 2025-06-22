import random
from typing import Dict, List, Any, Tuple, Optional, Set, Union
from collections import defaultdict, Counter
import numpy as np
from numba import jit, types # Removed unused imports: from numba.extending import typeof_impl, as_numba_type, models, register_model, make_attribute_wrapper, unbox, NativeValue, box
from numba import njit # Correct Numba decorator for nopython mode
# Removed: from contextlib import ExitStack

# --- Логгер ---
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# --- Константы ---
from game_server.config.provider import config

# ДОБАВЛЕНО: Импорт DTO
from game_server.common_contracts.start_orcestrator.dtos import CharacterBaseStatsData, CharacterRoleInputData, CharacterWithRoleArchetypeData #


# Numba-оптимизированная функция
# @jit(nopython=True, fastmath=True) # Оставляем закомментированным, чтобы избежать проблем с Numba 0.59.0 и str
# Если необходимо использовать nopython=True, то base_stats_names_array должен быть массивом int ID,
# а role_stat_priorities_flat массивом int ID, и сравнения должны быть по ID.
# Иначе, это будет компилироваться в object mode, или вызовет ошибку.
# Для простоты, пока оставим так, как было. Если производительность станет проблемой,
# нужно будет внедрять числовые ID для статов и ролей.
def _determine_single_character_role_optimized(
    base_stats_names_array: np.ndarray, # Массив имен статов (например, ["STR", "AGI", ...])
    base_stats_values_array: np.ndarray, # Массив значений статов (например, [10, 12, ...])
    role_names_array: np.ndarray, # Массив названий ролей
    role_stat_priorities_flat: np.ndarray, # Плоский массив приоритетов статов для всех ролей
    role_stat_priorities_indices: np.ndarray # Индексы для извлечения приоритетов из плоского массива
) -> int:
    """
    Вспомогательная функция: Определяет роль ОДНОГО персонажа на основе его SPECIAL-статов.
    Возвращает индекс лучшей роли в role_names_array.
    """
    num_stats = base_stats_names_array.shape[0]
    if num_stats < 3:
        return -1 # Соответствует UNASSIGNED_ROLE_INDEX

    sorted_indices = np.argsort(-base_stats_values_array)
    top_stat_indices = sorted_indices[:3]
    character_top_stats_names_raw = base_stats_names_array[top_stat_indices]

    best_match_role_index: int = -1
    max_score: int = -1

    num_roles = role_names_array.shape[0]

    for role_idx in range(num_roles):
        start_idx = role_stat_priorities_indices[role_idx]
        end_idx = role_stat_priorities_indices[role_idx + 1]
        role_stat_priority = role_stat_priorities_flat[start_idx:end_idx]

        if len(role_stat_priority) < 3:
            continue

        current_score = 0
        for i in range(min(3, len(character_top_stats_names_raw), len(role_stat_priority))):
            if character_top_stats_names_raw[i] == role_stat_priority[i]:
                current_score += (3 - i)

        if current_score > max_score:
            max_score = current_score
            best_match_role_index = role_idx
            
    return best_match_role_index


# ИЗМЕНЕНО: Принимает List[CharacterRoleInputData] и возвращает List[CharacterWithRoleArchetypeData]
def assign_roles_and_archetypes_to_character_batch(
    characters_data: List[CharacterRoleInputData] # <--- ИЗМЕНЕНО: Теперь принимает DTO
) -> List[CharacterWithRoleArchetypeData]: # <--- ИЗМЕНЕНО: Теперь возвращает DTO
    """
    Присваивает роль и архетип каждому персонажу в батче.
    """
    if not isinstance(characters_data, list):
        raise TypeError("characters_data должна быть списком DTO.")
    if not all(isinstance(char, CharacterRoleInputData) for char in characters_data): # Проверка на тип DTO
        raise TypeError("Все элементы в characters_data должны быть экземплярами CharacterRoleInputData.")

    # Предварительная обработка NPC_ROLES и NPC_ARCHETYPES для Numba
    all_role_names = [r_name for r_name in config.constants.character.NPC_ROLES.keys()] # ИЗМЕНЕНО: Доступ через config
    role_name_to_index = {name: i for i, name in enumerate(all_role_names)}
    role_names_np = np.array(all_role_names)

    role_stat_priorities_flat_list = []
    role_stat_priorities_indices_list = [0]
    for r_name in all_role_names:
        priority_list = config.constants.character.NPC_ROLES[r_name].get("stat_priority", []) # ИЗМЕНЕНО: Доступ через config
        role_stat_priorities_flat_list.extend(priority_list)
        role_stat_priorities_indices_list.append(len(role_stat_priorities_flat_list))
    
    role_stat_priorities_flat_np = np.array(role_stat_priorities_flat_list)
    role_stat_priorities_indices_np = np.array(role_stat_priorities_indices_list)

    all_archetype_names = [a_name for a_name in config.constants.character.NPC_ARCHETYPES.keys()] # ИЗМЕНЕНО: Доступ через config
    archetype_name_to_index = {name: i for i, name in enumerate(all_archetype_names)}
    archetype_names_np = np.array(all_archetype_names)

    archetype_weights = np.array([config.constants.character.NPC_ARCHETYPES.get(name, {}).get("weight", 1) for name in all_archetype_names], dtype=np.int32) # ИЗМЕНЕНО: Доступ через config
    
    processed_characters: List[CharacterWithRoleArchetypeData] = [] # <--- ИЗМЕНЕНО
    
    for char_input_dto in characters_data: # Итерируем по DTO
        # current_char_data = char_input_dto.copy() # Создаем изменяемую копию DTO
        
        if not char_input_dto.base_stats: # Проверяем DTO на наличие base_stats
            logger.warning(f"В assign_roles_and_archetypes: Пропущен элемент без 'base_stats'. Объект: {char_input_dto.dict()}") # Используем .dict()
            # Возвращаем DTO с дефолтными значениями
            processed_characters.append(
                CharacterWithRoleArchetypeData(
                    quality_level=char_input_dto.quality_level,
                    base_stats=char_input_dto.base_stats,
                    selected_role_name="UNASSIGNED_ROLE",
                    selected_archetype_name="UNASSIGNED_ARCHETYPE"
                )
            )
            continue

        base_stats_dto = char_input_dto.base_stats # Это уже CharacterBaseStatsData DTO
        
        # Преобразуем base_stats DTO в NumPy массивы для Numba
        stats_names = list(base_stats_dto.model_dump().keys()) # Используем .model_dump()
        stats_values = list(base_stats_dto.model_dump().values()) # Используем .model_dump()
        base_stats_names_np = np.array(stats_names)
        base_stats_values_np = np.array(stats_values, dtype=np.int32)

        # 1. Определяем роль с помощью оптимизированной функции
        selected_role_idx = _determine_single_character_role_optimized(
            base_stats_names_np,
            base_stats_values_np,
            role_names_np,
            role_stat_priorities_flat_np,
            role_stat_priorities_indices_np
        )
        
        selected_role = "UNASSIGNED_ROLE"
        if selected_role_idx != -1:
            selected_role = all_role_names[selected_role_idx]
            
        # 2. Определяем архетип на основе назначенной роли
        selected_archetype_name = "UNASSIGNED_ARCHETYPE"
        if selected_role != "UNASSIGNED_ROLE" and selected_role in config.constants.character.NPC_ROLES: # ИЗМЕНЕНО: Доступ через config
            role_definition = config.constants.character.NPC_ROLES[selected_role] # ИЗМЕНЕНО: Доступ через config
            archetype_affinities = role_definition.get("archetype_affinity", [])
            
            valid_affinities_indices = [
                archetype_name_to_index[arch_name] for arch_name in archetype_affinities if arch_name in config.constants.character.NPC_ARCHETYPES # ИЗМЕНЕНО: Доступ через config
            ]
            
            if valid_affinities_indices:
                if len(valid_affinities_indices) == 1:
                    selected_archetype_name = all_archetype_names[valid_affinities_indices[0]]
                else:
                    current_weights = archetype_weights[valid_affinities_indices]
                    
                    if np.sum(current_weights) > 0:
                        selected_archetype_name = np.random.choice(
                            [all_archetype_names[idx] for idx in valid_affinities_indices],
                            p=current_weights / np.sum(current_weights),
                            size=1
                        )[0]
                    elif valid_affinities_indices:
                        selected_archetype_name = random.choice([all_archetype_names[idx] for idx in valid_affinities_indices])
            
        # ИЗМЕНЕНО: Создаем CharacterWithRoleArchetypeData DTO
        processed_characters.append(
            CharacterWithRoleArchetypeData(
                quality_level=char_input_dto.quality_level,
                base_stats=char_input_dto.base_stats,
                selected_role_name=selected_role,
                selected_archetype_name=selected_archetype_name
            )
        )
    
    return processed_characters