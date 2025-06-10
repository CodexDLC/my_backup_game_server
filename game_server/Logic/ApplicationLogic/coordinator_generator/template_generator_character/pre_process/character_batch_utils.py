# game_server/Logic/InfrastructureLogic/generator/character_batch_utils.py

import random
from typing import Dict, List, Any
from collections import Counter

# Здесь больше не нужен импорт DEFAULT_RACE_WEIGHT, так как он берется из БД.
# Остальные импорты констант для других функций здесь могут быть:
# from ..constant.constant_character import (
#     TARGET_POOL_QUALITY_DISTRIBUTION,
#     CHARACTER_TEMPLATE_QUALITY_CONFIG
# )
# from ..generator_settings import DEFAULT_CHARACTER_GENDER_RATIO


def determine_genders_for_batch(
    num_to_generate_in_batch: int,
    current_gender_counts_in_pool: Dict[str, int],
    target_pool_total_size: int,
    desired_gender_ratio: float
) -> List[str]:
    # ... (логика этого метода остается без изменений) ...
    genders_for_batch: List[str] = []

    ideal_males_in_full_pool = round(target_pool_total_size * desired_gender_ratio)
    ideal_females_in_full_pool = target_pool_total_size - ideal_males_in_full_pool

    male_shortfall_total = max(0, ideal_males_in_full_pool - current_gender_counts_in_pool.get('MALE', 0))
    female_shortfall_total = max(0, ideal_females_in_full_pool - current_gender_counts_in_pool.get('FEMALE', 0))
    
    gender_shortfall_list_total_pool = ['MALE'] * male_shortfall_total + ['FEMALE'] * female_shortfall_total
    
    if len(gender_shortfall_list_total_pool) >= num_to_generate_in_batch:
        random.shuffle(gender_shortfall_list_total_pool)
        genders_for_batch = gender_shortfall_list_total_pool[:num_to_generate_in_batch]
    else:
        genders_for_batch.extend(gender_shortfall_list_total_pool)
        remaining_gender_slots = num_to_generate_in_batch - len(genders_for_batch)
        if remaining_gender_slots > 0:
            extra_males_for_batch = round(remaining_gender_slots * desired_gender_ratio)
            extra_females_for_batch = remaining_gender_slots - extra_males_for_batch
            genders_for_batch.extend(['MALE'] * extra_males_for_batch)
            genders_for_batch.extend(['FEMALE'] * extra_females_for_batch)
            genders_for_batch = genders_for_batch[:num_to_generate_in_batch] 
    
    random.shuffle(genders_for_batch)
    while len(genders_for_batch) < num_to_generate_in_batch:
        if random.random() < desired_gender_ratio:
            genders_for_batch.append('MALE')
        else:
            genders_for_batch.append('FEMALE')
    
    return genders_for_batch[:num_to_generate_in_batch]


def determine_qualities_for_batch(
    num_to_generate_in_batch: int,
    current_quality_counts_in_pool: Dict[str, int],
    target_pool_total_size: int,
    target_quality_distribution: Dict[str, float],
    character_template_quality_config: Dict[str, Any]
) -> List[str]:
    # ... (логика этого метода остается без изменений) ...
    qualities_for_batch: List[str] = []
    
    quality_shortfall_map: Dict[str, int] = {}
    all_defined_qualities = character_template_quality_config.keys()

    for q_name in all_defined_qualities:
        percentage = target_quality_distribution.get(q_name, 0.0)
        ideal_count = round(target_pool_total_size * percentage)
        current_count = current_quality_counts_in_pool.get(q_name, 0)
        needed = ideal_count - current_count
        quality_shortfall_map[q_name] = max(0, needed)

    temp_quality_shortfall_list = []
    for q_name, num_needed in quality_shortfall_map.items():
        if q_name in character_template_quality_config:
            temp_quality_shortfall_list.extend([q_name] * num_needed)
    
    total_shortfall_units = len(temp_quality_shortfall_list)

    if total_shortfall_units == 0 and num_to_generate_in_batch > 0:
        for q_name, perc in sorted(target_quality_distribution.items(), key=lambda x: x[1], reverse=True):
            if q_name in character_template_quality_config:
                count = round(num_to_generate_in_batch * perc)
                qualities_for_batch.extend([q_name] * count)
    elif total_shortfall_units >= num_to_generate_in_batch:
        random.shuffle(temp_quality_shortfall_list)
        qualities_for_batch = temp_quality_shortfall_list[:num_to_generate_in_batch]
    else: # total_shortfall_units < num_to_generate_in_batch
        qualities_for_batch.extend(temp_quality_shortfall_list)
        remaining_quality_slots = num_to_generate_in_batch - len(qualities_for_batch)
        if remaining_quality_slots > 0:
            sorted_target_qualities = [
                q[0] for q in sorted(target_quality_distribution.items(), key=lambda x: x[1], reverse=True)
                if q[0] in character_template_quality_config
            ]
            if not sorted_target_qualities:
                 sorted_target_qualities = list(character_template_quality_config.keys())

            if sorted_target_qualities:
                for i in range(remaining_quality_slots):
                    qualities_for_batch.append(sorted_target_qualities[i % len(sorted_target_qualities)])
            elif character_template_quality_config:
                 qualities_for_batch.extend([list(character_template_quality_config.keys())[0]] * remaining_quality_slots)
    
    priority_qualities_for_adjustment = [
        q[0] for q in sorted(target_quality_distribution.items(), key=lambda x: x[1], reverse=True)
        if q[0] in character_template_quality_config
    ]
    if not priority_qualities_for_adjustment and character_template_quality_config:
        priority_qualities_for_adjustment = list(character_template_quality_config.keys())


    while len(qualities_for_batch) < num_to_generate_in_batch:
        if priority_qualities_for_adjustment:
            qualities_for_batch.append(random.choice(priority_qualities_for_adjustment))
        elif character_template_quality_config:
            qualities_for_batch.append(list(character_template_quality_config.keys())[0])
        else:
            break 
            
    if len(qualities_for_batch) > num_to_generate_in_batch:
        random.shuffle(qualities_for_batch)
        qualities_for_batch = qualities_for_batch[:num_to_generate_in_batch]

    random.shuffle(qualities_for_batch)
    return qualities_for_batch


def distribute_creature_types_for_batch(
    playable_races_data: List[Dict[str, Any]], 
    num_to_generate_in_batch: int
) -> List[str]:
    """
    Распределяет типы существ (расы) для генерируемого батча,
    учитывая их веса (rarity_weight) для неравномерного распределения.
    Возвращает список creature_type_id.
    """
    creature_types_for_batch: List[str] = []

    if not playable_races_data:
        print("Предупреждение: Список playable_races_data пуст. Невозможно распределить типы.")
        return []

    # Если раса всего одна, просто равномерно заполняем ею батч, используя её ID
    if len(playable_races_data) == 1:
        single_race_id = playable_races_data[0]["creature_type_id"]
        return [single_race_id] * num_to_generate_in_batch

    # --- Логика распределения по весам ---
    # Создаем список пар (creature_type_id, weight)
    weighted_races = []
    for race_data in playable_races_data:
        # ИСПОЛЬЗУЕМ rarity_weight из данных расы.
        # Если rarity_weight отсутствует или не является числом, используем DEFAULT_WEIGHT_FOR_MISSING_RARITY.
        # Эту константу DEFAULT_WEIGHT_FOR_MISSING_RARITY нужно будет определить в generator_settings.py.
        weight = race_data.get("rarity_weight")
        if not isinstance(weight, (int, float)) or weight < 0:
            # Fallback к значению по умолчанию, если вес некорректен
            # Заглушка для импорта: from ..generator_settings import DEFAULT_WEIGHT_FOR_MISSING_RARITY
            # Если DEFAULT_WEIGHT_FOR_MISSING_RARITY не будет, то временно используем 1
            weight = 100 # Временно используем 100, пока не определим в settings
            print(f"Предупреждение: rarity_weight для {race_data.get('name', 'Неизвестная раса')} некорректен или отсутствует. Используется вес по умолчанию: {weight}")

        weighted_races.append((race_data["creature_type_id"], weight))
    
    total_weight = sum(weight for _, weight in weighted_races)
    
    if total_weight <= 0:
        print("Предупреждение: Сумма весов рас равна нулю или отрицательна. Распределение будет равномерным по доступным ID.")
        # Fallback к равномерному распределению по ID, если веса не работают
        available_ids = [race_data["creature_type_id"] for race_data in playable_races_data]
        random.shuffle(available_ids)
        for i in range(num_to_generate_in_batch):
            creature_types_for_batch.append(available_ids[i % len(available_ids)])
        return creature_types_for_batch


    # Используем random.choices для выбора на основе весов
    creature_type_ids, weights = zip(*weighted_races)
    creature_types_for_batch = random.choices(
        population=creature_type_ids,
        weights=weights,
        k=num_to_generate_in_batch
    )
    
    return creature_types_for_batch