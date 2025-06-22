# game_server\config\settings\character\generator_settings.py
from typing import Dict, Any

# --- Целевое распределение УРОВНЕЙ КАЧЕСТВА ШАБЛОНА в ОБЩЕМ ПУЛЕ ---
# Генератор будет стремиться поддерживать это распределение. Сумма должна быть 1.0.
TARGET_POOL_QUALITY_DISTRIBUTION: Dict[str, float] = {
    "SUPERIOR_ELITE_QUALITY": 0.001,  # 0.1%
    "ELITE_QUALITY": 0.059,         # 5.9%
    "ADVANCED_QUALITY": 0.14,         # 14%
    "STANDARD_QUALITY": 0.25,         # 25%
    "BASIC_QUALITY": 0.55           # 55%
}


# --- Определение УРОВНЕЙ КАЧЕСТВА ШАБЛОНА персонажа и их параметров ---
# Этот словарь описывает различные уровни базового качества для генерируемых персонажей.
CHARACTER_TEMPLATE_QUALITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "SUPERIOR_ELITE_QUALITY": { # 5-й уровень силы (наивысшее качество)
        "max_total_skill_points": 15,
        "max_skill_level_per_skill": 3,
        "min_active_skills": 5,
        "max_active_skills": 10,
        "flat_bonus_per_stat_config": {"type": "fixed", "value": 1},
        "max_duplicate_stat_values": 2,
        "base_stat_max_value_per_stat": 19,
        "min_stat_value_floor": 4,
    },
    "ELITE_QUALITY": { # 4-й уровень силы
        "max_total_skill_points": 12,
        "max_skill_level_per_skill": 3,
        "min_active_skills": 4,
        "max_active_skills": 10,
        "flat_bonus_per_stat_config": {"type": "coin_flip", "options": [0, 1]},
        "max_duplicate_stat_values": 2,
        "base_stat_max_value_per_stat": 19,
        "min_stat_value_floor": 3,
    },
    "ADVANCED_QUALITY": { # 3-й уровень силы
        "max_total_skill_points": 10,
        "max_skill_level_per_skill": 2,
        "min_active_skills": 5,
        "max_active_skills": 9,
        "flat_bonus_per_stat_config": {"type": "fixed", "value": 0},
        "max_duplicate_stat_values": 1,
        "base_stat_max_value_per_stat": 18,
        "min_stat_value_floor": 3,
    },
    "STANDARD_QUALITY": { # 2-й уровень силы
        "max_total_skill_points": 8,
        "max_skill_level_per_skill": 2,
        "min_active_skills": 5,
        "max_active_skills": 5,
        "flat_bonus_per_stat_config": {"type": "coin_flip", "options": [0, -1]},
        "max_duplicate_stat_values": 1,
        "base_stat_max_value_per_stat": 17,
        "min_stat_value_floor": 2,
    },
    "BASIC_QUALITY": { # 1-й уровень силы (самое слабое качество)
        "max_total_skill_points": 5,
        "max_skill_level_per_skill": 1,
        "min_active_skills": 5,
        "max_active_skills": 5,
        "flat_bonus_per_stat_config": {"type": "fixed", "value": -1},
        "max_duplicate_stat_values": 1,
        "base_stat_max_value_per_stat": 17,
        "min_stat_value_floor": 2,
    }
}