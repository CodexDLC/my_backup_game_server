# game_server/core/constants_generator.py

from typing import Dict, Any, List


# --- Определение УРОВНЕЙ КАЧЕСТВА ШАБЛОНА персонажа и их параметров ---
# Этот словарь описывает различные уровни базового качества для генерируемых персонажей.
# Он определяет их потенциал, бюджеты и максимальные уровни для статов и скиллов.
# Это ключевой параметр, который определяет "мощность" генерируемой болванки.
from typing import Dict, Any

CHARACTER_TEMPLATE_QUALITY_CONFIG: Dict[str, Dict[str, Any]] = {
    # Общая конфигурация для всех бросков кубиков.
    # Эта секция будет использоваться для всех качеств.
    "BASE_ROLL_CONFIG": {
        "num_rolls": 3,
        "dice_type": 6,
        "drop_lowest": 0,
    },

    "SUPERIOR_ELITE_QUALITY": { # 5-й уровень силы (наивысшее качество)
        # --- Параметры навыков (из твоих старых данных) ---
        "max_total_skill_points": 15,
        "max_skill_level_per_skill": 3,
        "min_active_skills": 5,
        "max_active_skills": 10,
        # --- Параметры SPECIAL-статов (обновленные) ---
        "flat_bonus_per_stat_config": {"type": "fixed", "value": 1}, # ВСЕГДА +1 к 3d6 (диапазон от 4 до 19)
        "max_duplicate_stat_values": 2, # Допускается до 2 одинаковых значений в наборе из 7
        "base_stat_max_value_per_stat": 19, # Максимальное значение для каждого стата
        "min_stat_value_floor": 4, # Минимальное значение, ниже которого стат не опустится
    },
    "ELITE_QUALITY": { # 4-й уровень силы
        # --- Параметры навыков (из твоих старых данных) ---
        "max_total_skill_points": 12,
        "max_skill_level_per_skill": 3,
        "min_active_skills": 4,
        "max_active_skills": 10,
        # --- Параметры SPECIAL-статов (обновленные) ---
        "flat_bonus_per_stat_config": {"type": "coin_flip", "options": [0, 1]}, # МОНЕТКА: +0 или +1 к 3d6
        "max_duplicate_stat_values": 2, # Допускается до 2 одинаковых значений
        "base_stat_max_value_per_stat": 19,
        "min_stat_value_floor": 3,
    },
    "ADVANCED_QUALITY": { # 3-й уровень силы
        # --- Параметры навыков (из твоих старых данных) ---
        "max_total_skill_points": 10,
        "max_skill_level_per_skill": 2,
        "min_active_skills": 5,
        "max_active_skills": 9,
        # --- Параметры SPECIAL-статов (обновленные) ---
        "flat_bonus_per_stat_config": {"type": "fixed", "value": 0}, # ЧИСТЫЕ КУБИКИ: 3d6 (диапазон от 3 до 18)
        "max_duplicate_stat_values": 1, # Все значения должны быть уникальными
        "base_stat_max_value_per_stat": 18,
        "min_stat_value_floor": 3,
    },
    "STANDARD_QUALITY": { # 2-й уровень силы
        # --- Параметры навыков (из твоих старых данных) ---
        "max_total_skill_points": 8,
        "max_skill_level_per_skill": 2,
        "min_active_skills": 5,
        "max_active_skills": 5,
        # --- Параметры SPECIAL-статов (обновленные) ---
        "flat_bonus_per_stat_config": {"type": "coin_flip", "options": [0, -1]}, # МОНЕТКА: +0 или -1 к 3d6
        "max_duplicate_stat_values": 1, # Все значения должны быть уникальными
        "base_stat_max_value_per_stat": 17,
        "min_stat_value_floor": 2,
    },
    "BASIC_QUALITY": { # 1-й уровень силы (самое слабое качество)
        # --- Параметры навыков (из твоих старых данных) ---
        "max_total_skill_points": 5,
        "max_skill_level_per_skill": 1,
        "min_active_skills": 5,
        "max_active_skills": 5,
        # --- Параметры SPECIAL-статов (обновленные) ---
        "flat_bonus_per_stat_config": {"type": "fixed", "value": -1}, # ВСЕГДА -1 к 3d6 (диапазон от 2 до 17)
        "max_duplicate_stat_values": 1, # Все значения должны быть уникальными
        "base_stat_max_value_per_stat": 17,
        "min_stat_value_floor": 2,
    }
}

# --- Целевое распределение УРОВНЕЙ КАЧЕСТВА ШАБЛОНА в ОБЩЕМ ПУЛЕ ---
# Генератор будет стремиться поддерживать это распределение в пуле MAX_CHARACTER_POOL_SIZE.
# Сумма всех значений должна быть 1.0.
TARGET_POOL_QUALITY_DISTRIBUTION: Dict[str, float] = {
    "SUPERIOR_ELITE_QUALITY": 0.001,  # 0.1%
    "ELITE_QUALITY": 0.059,         # 5.9%
    "ADVANCED_QUALITY": 0.14,       # 14%
    "STANDARD_QUALITY": 0.25,       # 25%
    "BASIC_QUALITY": 0.55           # 55%
}

# --- КОНСТАНТЫ ДЛЯ ХАРАКТЕРИСТИК (SPECIAL Stats) ---
# Список всех 7 основных характеристик персонажа.
SPECIAL_STATS: List[str] = [
    "STRENGTH",    # S
    "PERCEPTION",  # P
    "ENDURANCE",   # E
    "CHARISMA",    # C
    "INTELLIGENCE",# I
    "AGILITY",     # A
    "LUCK"         # L
]

# --- Определение групп навыков и их ограничений (Skill Group Limits) ---
# Этот словарь определяет правила для групп навыков.
# 'limit_type': "exclusive" - можно выбрать только один навык из этой группы.
#             "any"      - можно выбрать до 'limit_value' навыков из этой группы.
# 'limit_value': Максимальное количество навыков, которое может быть выбрано из группы.
SKILL_GROUP_LIMITS: Dict[str, Dict[str, Any]] = {
    "magic_elemental": {"limit_type": "exclusive", "limit_value": 1}, # Только 1 стихия
    "combat_weapon": {"limit_type": "exclusive", "limit_value": 1},   # Только 1 тип оружия (ближний бой/дальний бой)
    "armor_type_proficiency": {"limit_type": "exclusive", "limit_value": 1}, # Только 1 тип брони (легкая/средняя/тяжелая)
    "shield_proficiency": {"limit_type": "exclusive", "limit_value": 1}, # Только 1 тип щита (легкий/средний/тяжелый)
    "tactical_core_combat": {"limit_type": "any", "limit_value": 2}, # Максимум 2 из основных боевых тактик
    "tactical_resilience": {"limit_type": "any", "limit_value": 1}, # Максимум 1 из навыков устойчивости
    "magic_special": {"limit_type": "exclusive", "limit_value": 1}, # Только 1 специальная магия (темная/светлая/арканная)
    "gathering_utility": {"limit_type": "any", "limit_value": 3}, # До 3 утилитарных навыков сбора
    "gathering_combat": {"limit_type": "exclusive", "limit_value": 1}, # Только 1 боевой навык сбора (охота/рыбалка)
    "crafting_production": {"limit_type": "any", "limit_value": 2}, # До 2 производственных ремесел
    "social_cooperation_orientation": {"limit_type": "exclusive", "limit_value": 1}, # НОВАЯ ГРУППА: Только 1 социальная ориентация (лидерство ИЛИ эгоизм)
}


# --- КОНСТАНТЫ ДЛЯ АРХЕТИПОВ NPC (NPC Archetypes) ---
NPC_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "COMBAT_FOCUSED": {
        "weight": 0.5,
        "skill_preference_tags": ["combat", "weapon_use", "defense", "tactical", "survival", "magic"],
        "description": "Склонен к навыкам, связанным с боем, выживанием и самозащитой."
    },
    "PEACEFUL_FOCUSED": {
        "weight": 0.5,
        "skill_preference_tags": ["social", "crafting", "utility", "knowledge", "gathering", "barter", "healing", "magic"],
        "description": "Склонен к навыкам, связанным с торговлей, ремеслами, наукой и общением."
    }
}

# --- КОНСТАНТЫ ДЛЯ РОЛЕЙ NPC (NPC Roles) ---
NPC_ROLES: Dict[str, Dict[str, Any]] = {
    "TRADER": {
        "weight": 0.10,
        "skill_preference_tags": {
            "limit_groups": [], # Нет строгих взаимоисключающих групп для трейдера
            "specific_skills": ["trader", "negotiator"] # Предпочтение конкретных навыков
        },
        "description": "Специализируется на торговле и экономических операциях.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["CHARISMA", "INTELLIGENCE", "LUCK"]
    },
    "CRAFTER": {
        "weight": 0.08,
        "skill_preference_tags": {
            "limit_groups": ["crafting_production"], # Обязательна 1-2 производственных навыка
            "specific_skills": ["weaponsmith", "armorsmith"] # Предпочтение оружейника и бронника
        },
        "description": "Занимается созданием и ремонтом предметов, с упором на оружие и броню.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["INTELLIGENCE", "AGILITY", "PERCEPTION"]
    },
    "GATHERER": {
        "weight": 0.10,
        "skill_preference_tags": {
            "limit_groups": ["gathering_utility"], # Обязателен 1-3 навыка сбора
            "specific_skills": ["forager", "herbalist"] # Предпочтение собирателя и травника
        },
        "description": "Собирает природные ресурсы и выживает в дикой местности.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["PERCEPTION", "ENDURANCE", "LUCK"]
    },
    "WARRIOR": {
        "weight": 0.20,
        "skill_preference_tags": {
            "limit_groups": ["combat_weapon", "armor_type_proficiency"], # Обязателен 1 тип оружия И 1 тип брони
            "specific_skills": ["slashing_weapon_user", "heavy_armor_user"] # Предпочтение рубящего оружия и тяжелой брони (пример, можно поменять)
        },
        "description": "Мастер ближнего боя и защиты, предпочитающий тяжелую броню.",
        "archetype_affinity": ["COMBAT_FOCUSED"],
        "stat_priority": ["STRENGTH", "ENDURANCE", "AGILITY"]
    },
    "RANGER": {
        "weight": 0.15,
        "skill_preference_tags": {
            "limit_groups": ["combat_weapon", "gathering_combat"], # Обязателен 1 тип оружия И 1 боевой навык сбора
            "specific_skills": ["ranged_master", "hunter"] # Предпочтение дальнобойного оружия и охоты
        },
        "description": "Специалист по дальнему бою, скрытности и выживанию в дикой местности.",
        "archetype_affinity": ["COMBAT_FOCUSED"],
        "stat_priority": ["PERCEPTION", "AGILITY", "ENDURANCE"]
    },
    "HEALER": {
        "weight": 0.07,
        "skill_preference_tags": {
            "limit_groups": [], # Нет строгих взаимоисключающих групп
            "specific_skills": ["healer", "light_mage"] # Предпочтение целителя и магии света
        },
        "description": "Использует целительские и поддерживающие навыки, включая магию света.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["CHARISMA", "INTELLIGENCE", "PERCEPTION"]
    },
    "ELEMENTALIST": {
        "weight": 0.07,
        "skill_preference_tags": {
            "limit_groups": ["magic_elemental", "armor_type_proficiency"], # Обязательна 1 стихия И 1 тип брони
            "specific_skills": ["pyromancer", "light_armor_user"] # Предпочтение пиромантии и легкой брони
        },
        "description": "Владеет силами природы и стихийной магией, предпочитая легкую броню.",
        "archetype_affinity": ["COMBAT_FOCUSED"],
        "stat_priority": ["INTELLIGENCE", "PERCEPTION", "AGILITY"]
    },
    "SCHOLAR": {
        "weight": 0.08,
        "skill_preference_tags": {
            "limit_groups": [], # Нет строгих взаимоисключающих групп
            "specific_skills": ["scientist", "arcane_scholar"] # Предпочтение ученого и арканного адепта
        },
        "description": "Посвящает себя изучению мира, знаний и магии.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["INTELLIGENCE", "PERCEPTION", "CHARISMA"]
    },
    "LEADER": {
        "weight": 0.08,
        "skill_preference_tags": {
            "limit_groups": ["social_cooperation_orientation"], # Обязательна 1 социальная ориентация (лидерство ИЛИ эгоизм)
            "specific_skills": ["leader", "negotiator", "organizer", "team_player"] # Предпочтение лидерства, переговоров, организации, командной работы
        },
        "description": "Обладает навыками управления, убеждения и организации других.",
        "archetype_affinity": ["COMBAT_FOCUSED", "PEACEFUL_FOCUSED"], # Лидер может быть как боевым, так и мирным
        "stat_priority": ["CHARISMA", "INTELLIGENCE", "LUCK"]
    }
}




