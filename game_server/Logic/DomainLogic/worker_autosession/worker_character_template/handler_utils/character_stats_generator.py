# game_server/Logic/InfrastructureLogic/generator/character_template_generator/utils/stat_generator.py
# (файл: worker_character_template/handler_utils/character_stats_generator.py)

import random
from typing import Dict, List

from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_character import CHARACTER_TEMPLATE_QUALITY_CONFIG, SPECIAL_STATS 

def generate_generated_base_stats(quality_level: str) -> Dict[str, int]:
    """
    Генерирует SPECIAL-статы для персонажа на основе его уровня качества,
    используя фиксированный 3d6 бросок и динамический flat_bonus_per_stat,
    а также контролируя дубликаты внутри набора статов.
    """
    if quality_level not in CHARACTER_TEMPLATE_QUALITY_CONFIG:
        raise ValueError(f"Неизвестный уровень качества: {quality_level}")

    config = CHARACTER_TEMPLATE_QUALITY_CONFIG[quality_level]
    base_roll_config = CHARACTER_TEMPLATE_QUALITY_CONFIG["BASE_ROLL_CONFIG"] #

    # Параметры из конфига для текущего качества
    flat_bonus_per_stat_config = config["flat_bonus_per_stat_config"] #
    max_duplicate_stat_values = config["max_duplicate_stat_values"] #
    base_stat_max_value_per_stat = config["base_stat_max_value_per_stat"] #
    min_stat_value_floor = config["min_stat_value_floor"] #

    # Параметры из BASE_ROLL_CONFIG
    num_rolls = base_roll_config["num_rolls"] #
    dice_type = base_roll_config["dice_type"] #
    drop_lowest = base_roll_config["drop_lowest"] #
    
    # Шаг 0: Определение flat_bonus_per_stat для текущей генерации персонажа
    current_flat_bonus: int
    if flat_bonus_per_stat_config["type"] == "fixed": #
        current_flat_bonus = flat_bonus_per_stat_config["value"] #
    elif flat_bonus_per_stat_config["type"] == "coin_flip": #
        current_flat_bonus = random.choice(flat_bonus_per_stat_config["options"]) #
    else:
        raise ValueError(f"Неизвестный тип flat_bonus_per_stat_config: {flat_bonus_per_stat_config['type']}")

    # Шаг 1: Генерация 7 Начальных Значений с Учетом Дубликатов (ВНУТРИ НАБОРА)
    generated_candidate_values: List[int] = []
    
    for _ in range(len(SPECIAL_STATS)): # Генерируем 7 статов по очереди
        attempt = 0
        max_attempts = 50 # Максимальное количество попыток найти допустимое значение

        while attempt < max_attempts:
            rolls: List[int] = []
            for _ in range(num_rolls): #
                rolls.append(random.randint(1, dice_type)) #
            
            if drop_lowest > 0: #
                rolls.sort()
                rolls = rolls[drop_lowest:]

            value = sum(rolls) + current_flat_bonus
            
            # Обрезаем значение до min_stat_value_floor и base_stat_max_value_per_stat
            value = max(min_stat_value_floor, value) #
            value = min(value, base_stat_max_value_per_stat) #

            # Проверяем условия дублирования в списке УЖЕ сгенерированных значений
            current_duplicates_of_this_value = generated_candidate_values.count(value)

            if current_duplicates_of_this_value < max_duplicate_stat_values: #
                generated_candidate_values.append(value)
                break # Значение найдено, переходим к следующему стату
            else:
                attempt += 1 # Попытка не удалась, пробуем еще раз

        else: # Если цикл while завершился без break (достигнут max_attempts)
            # Если не удалось найти допустимое значение за max_attempts,
            # мы добавляем текущее значение, даже если оно дублируется,
            # чтобы избежать зависания и обеспечить, что список будет из 7 элементов.
            generated_candidate_values.append(value) 
            # Можно добавить логирование предупреждения здесь, если нужно.

    # Шаг 2: Применение к Случайно Перемешанным Статам
    final_generated_stats: Dict[str, int] = {}
    shuffled_stats = list(SPECIAL_STATS)
    random.shuffle(shuffled_stats)

    for i, stat_name in enumerate(shuffled_stats):
        final_generated_stats[stat_name] = generated_candidate_values[i]
    
    return final_generated_stats