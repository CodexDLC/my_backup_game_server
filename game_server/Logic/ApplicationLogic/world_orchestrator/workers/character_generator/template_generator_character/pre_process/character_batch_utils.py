# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/template_generator_character/pre_process/character_batch_utils.py

import random
from typing import Dict, List, Any
from collections import Counter

# Импорт логгера
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.config.settings.process.prestart import DEFAULT_WEIGHT_FOR_MISSING_RARITY
from game_server.contracts.dtos.orchestrator.data_models import PlayableRaceData

# ДОБАВЛЕН ИМПОРТ DTO PlayableRaceData



def determine_genders_for_batch(
    num_to_generate_in_batch: int,
    current_gender_counts_in_pool: Dict[str, int],
    target_pool_total_size: int,
    desired_gender_ratio: float
) -> List[str]:
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
    playable_races_data: List[PlayableRaceData], # ИЗМЕНЕНО: тип на List[PlayableRaceData]
    num_to_generate_in_batch: int
) -> List[str]:
    """
    Распределяет типы существ (расы) для генерируемого батча,
    учитывая их веса (rarity_weight) для неравномерного распределения.
    Возвращает список creature_type_id.
    """
    creature_types_for_batch: List[str] = []

    if not playable_races_data:
        logger.warning("Предупреждение: Список playable_races_data пуст. Невозможно распределить типы.")
        return []

    if len(playable_races_data) == 1:
        # ИСПРАВЛЕНО: Доступ к атрибуту через точку и использование creature_type_id
        single_race_id = playable_races_data[0].creature_type_id
        return [str(single_race_id)] * num_to_generate_in_batch

    weighted_races = []
    for race_data in playable_races_data: # race_data теперь PlayableRaceData объект
        weight = race_data.rarity_weight # Доступ к атрибуту через точку
        if not isinstance(weight, (int, float)) or weight < 0:
            weight = DEFAULT_WEIGHT_FOR_MISSING_RARITY
            logger.warning(f"rarity_weight для {race_data.name} некорректен или отсутствует. Используется вес по умолчанию: {weight}") # Доступ к атрибуту через точку

        # ИСПРАВЛЕНО: Доступ к атрибуту через точку и использование creature_type_id
        weighted_races.append((str(race_data.creature_type_id), weight))
    
    total_weight = sum(weight for _, weight in weighted_races)
    
    if total_weight <= 0:
        logger.warning("Предупреждение: Сумма весов рас равна нулю или отрицательна. Распределение будет равномерным по доступным ID.")
        # ИСПРАВЛЕНО: Доступ к атрибуту через точку и использование creature_type_id
        available_ids = [str(race_data.creature_type_id) for race_data in playable_races_data]
        random.shuffle(available_ids)
        for i in range(num_to_generate_in_batch):
            creature_types_for_batch.append(available_ids[i % len(available_ids)])
        return creature_types_for_batch


    creature_type_ids, weights = zip(*weighted_races)
    creature_types_for_batch = random.choices(
        population=creature_type_ids,
        weights=weights,
        k=num_to_generate_in_batch
    )
    
    return creature_types_for_batch