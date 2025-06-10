# game_server\Logic\DomainLogic\handlers_template\worker_character_template\handler_utils\character_role_selector.py

import random
from typing import Dict, List, Any

from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_character import NPC_ARCHETYPES, NPC_ROLES

# Добавляем NPC_ARCHETYPES в импорты


def _determine_single_character_role(base_stats: Dict[str, int]) -> str:
    """
    Вспомогательная функция: Определяет роль ОДНОГО персонажа на основе его SPECIAL-статов.
    """
    if not base_stats or len(base_stats) < 3:
        return "UNASSIGNED_ROLE" # Изменено для ясности

    sorted_character_stats = sorted(
        base_stats.items(),
        key=lambda item: (-item[1], item[0]) 
    )
    character_top_stats_names = [stat_name for stat_name, _ in sorted_character_stats[:3]]

    best_match_role: str = "UNASSIGNED_ROLE" # Изменено для ясности
    max_score: int = -1

    for role_name, role_data in NPC_ROLES.items():
        role_stat_priority: List[str] = role_data.get("stat_priority", [])
        if not role_stat_priority or len(role_stat_priority) < 3:
            continue

        current_score = 0
        for i in range(min(3, len(character_top_stats_names), len(role_stat_priority))):
            if character_top_stats_names[i] == role_stat_priority[i]:
                current_score += (3 - i)

        if current_score > max_score:
            max_score = current_score
            best_match_role = role_name
            
    return best_match_role


def assign_roles_and_archetypes_to_character_batch( # <--- Переименуем функцию для ясности
    characters_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Присваивает роль и архетип каждому персонажу в батче.
    Роль определяется на основе SPECIAL-статов ('base_stats').
    Архетип определяется на основе 'archetype_affinity' назначенной роли.
    Возвращает новый список с обновленными словарями персонажей.
    """
    if not isinstance(characters_data, list):
        raise TypeError("characters_data должна быть списком словарей.")

    processed_characters: List[Dict[str, Any]] = []
    
    for char_data in characters_data:
        current_char_data = char_data.copy() 

        if "base_stats" not in current_char_data or not isinstance(current_char_data["base_stats"], dict):
            print(f"Предупреждение: В assign_roles_and_archetypes: Пропущен элемент без 'base_stats'. "
                  f"Объект: {current_char_data.get('id', 'Неизвестный ID')}")
            current_char_data["selected_role_name"] = "UNASSIGNED_ROLE"
            current_char_data["selected_archetype_name"] = "UNASSIGNED_ARCHETYPE"
            processed_characters.append(current_char_data)
            continue

        base_stats = current_char_data["base_stats"]
        
        # 1. Определяем роль
        selected_role = _determine_single_character_role(base_stats)
        current_char_data["selected_role_name"] = selected_role
        
        # 2. Определяем архетип на основе назначенной роли
        selected_archetype_name = "UNASSIGNED_ARCHETYPE" # Значение по умолчанию
        if selected_role != "UNASSIGNED_ROLE" and selected_role in NPC_ROLES:
            role_definition = NPC_ROLES[selected_role]
            archetype_affinities = role_definition.get("archetype_affinity", [])
            
            valid_affinities = [
                arch_name for arch_name in archetype_affinities if arch_name in NPC_ARCHETYPES
            ]
            
            if valid_affinities:
                if len(valid_affinities) == 1:
                    selected_archetype_name = valid_affinities[0]
                else:
                    # Взвешенный случайный выбор, если у архетипов есть веса
                    weights = []
                    for arch_name in valid_affinities:
                        archetype_def = NPC_ARCHETYPES.get(arch_name, {})
                        weights.append(archetype_def.get("weight", 1)) # По умолчанию вес 1
                    
                    # Проверка, что сумма весов не ноль, чтобы избежать ошибки в random.choices
                    if sum(weights) > 0 :
                         selected_archetype_name = random.choices(valid_affinities, weights=weights, k=1)[0]
                    elif valid_affinities: # Если все веса 0, но есть валидные архетипы, выбираем случайно
                         selected_archetype_name = random.choice(valid_affinities)
                    # Если valid_affinities пуст после фильтрации, selected_archetype_name останется UNASSIGNED_ARCHETYPE
            # else: (Если нет affinities у роли или они все невалидны)
            # selected_archetype_name останется "UNASSIGNED_ARCHETYPE"
        
        current_char_data["selected_archetype_name"] = selected_archetype_name
        processed_characters.append(current_char_data)
    
    return processed_characters