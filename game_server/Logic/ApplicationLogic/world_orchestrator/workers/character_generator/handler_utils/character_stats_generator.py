import random
from typing import Dict, List, Any, Tuple
import numpy as np
from numba import jit, int32

# --- Импорты констант и конфига ---
from game_server.config.provider import config
from game_server.contracts.dtos.orchestrator.data_models import CharacterBaseStatsData


# Выносим часть логики, которую Numba может компилировать
@jit(nopython=True, fastmath=True)
def _generate_single_stat_value(
    num_rolls: int,
    dice_type: int,
    drop_lowest: int,
    current_flat_bonus: int,
    min_stat_value_floor: int,
    base_stat_max_value_per_stat: int,
    max_duplicate_stat_values: int,
    existing_values_array: np.ndarray,
    num_existing_values: int
) -> int:
    """
    Генерирует одно значение стата с учетом всех правил,
    оптимизировано с Numba.
    """
    attempt = 0
    max_attempts = 50

    while attempt < max_attempts:
        rolls = np.random.randint(1, dice_type + 1, size=num_rolls)

        if drop_lowest > 0:
            sorted_rolls = np.sort(rolls)
            rolls_sum = np.sum(sorted_rolls[drop_lowest:])
        else:
            rolls_sum = np.sum(rolls)

        value = rolls_sum + current_flat_bonus

        value = max(min_stat_value_floor, value)
        value = min(value, base_stat_max_value_per_stat)

        current_duplicates_of_this_value = np.sum(existing_values_array[:num_existing_values] == value)

        if current_duplicates_of_this_value < max_duplicate_stat_values:
            return value
        else:
            attempt += 1

    return value


def generate_generated_base_stats(quality_level: str) -> CharacterBaseStatsData:
    """
    Генерирует SPECIAL-статы для персонажа на основе его уровня качества,
    используя фиксированный 3d6 бросок и динамический flat_bonus_per_stat,
    а также контролируя дубликаты внутри набора статов.
    Оптимизировано с использованием Numba и NumPy.
    Возвращает CharacterBaseStatsData DTO.
    """
    if quality_level not in config.settings.character.CHARACTER_TEMPLATE_QUALITY_CONFIG:
        raise ValueError(f"Неизвестный уровень качества: {quality_level}")

    config_data = config.settings.character.CHARACTER_TEMPLATE_QUALITY_CONFIG[quality_level]
    base_roll_config = config.constants.character.BASE_ROLL_CONFIG

    flat_bonus_per_stat_config = config_data["flat_bonus_per_stat_config"]
    max_duplicate_stat_values = config_data["max_duplicate_stat_values"]
    base_stat_max_value_per_stat = config_data["base_stat_max_value_per_stat"]
    min_stat_value_floor = config_data["min_stat_value_floor"]

    num_rolls = base_roll_config["num_rolls"]
    dice_type = base_roll_config["dice_type"]
    drop_lowest = base_roll_config["drop_lowest"]

    current_flat_bonus: int
    if flat_bonus_per_stat_config["type"] == "fixed":
        current_flat_bonus = flat_bonus_per_stat_config["value"]
    elif flat_bonus_per_stat_config["type"] == "coin_flip":
        current_flat_bonus = random.choice(flat_bonus_per_stat_config["options"])
    else:
        raise ValueError(f"Неизвестный тип flat_bonus_per_stat_config: {flat_bonus_per_stat_config['type']}")

    generated_candidate_values_np = np.zeros(len(config.constants.character.SPECIAL_STATS), dtype=np.int32)
    
    for i in range(len(config.constants.character.SPECIAL_STATS)):
        value = _generate_single_stat_value(
            num_rolls,
            dice_type,
            drop_lowest,
            current_flat_bonus,
            min_stat_value_floor,
            base_stat_max_value_per_stat,
            max_duplicate_stat_values,
            generated_candidate_values_np,
            i
        )
        generated_candidate_values_np[i] = value
        
    final_generated_stats_dict: Dict[str, int] = {}
    
    shuffled_stats = list(config.constants.character.SPECIAL_STATS)
    random.shuffle(shuffled_stats)

    for i, stat_name in enumerate(shuffled_stats):
        final_generated_stats_dict[stat_name] = int(generated_candidate_values_np[i])
    
    # --- ИЗМЕНЕНИЕ: Исправлена проблема с регистром ключей ---
    
    # 1. Создаем новый словарь с ключами в нижнем регистре
    stats_for_dto = {key.lower(): value for key, value in final_generated_stats_dict.items()}

    # 2. Распаковываем словарь с уже правильными ключами в конструктор DTO
    return CharacterBaseStatsData(**stats_for_dto)