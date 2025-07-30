from typing import Dict, Final, List, Any

# Константы опыта для достижения следующего уровня (сейчас не используются, но заложены на будущее)
SKILL_XP_PER_LEVEL: Final[Dict[int, int]] = {
    1: 100,
    2: 107,
    3: 114,
    4: 122,
    5: 131,
    6: 140,
    7: 150,
    8: 160,
    9: 171,
    10: 183,
    11: 196,
    12: 210,
    13: 225,
    14: 240,
    15: 257,
    16: 275,
    17: 295,
    18: 315,
    19: 337,
    20: 361,
    21: 386,
    22: 414,
    23: 443,
    24: 474,
    25: 507,
    26: 542,
    27: 580,
    28: 621,
    29: 664,
    30: 711,
    31: 761,
    32: 814,
    33: 871,
    34: 932,
    35: 997,
    36: 1067,
    37: 1142,
    38: 1222,
    39: 1307,
    40: 1399,
    41: 1497,
    42: 1602,
    43: 1714,
    44: 1834,
    45: 1962,
    46: 2100,
    47: 2247,
    48: 2404,
    49: 2572,
    50: 2752,
    51: 2945,
    52: 3151,
    53: 3372,
    54: 3608,
    55: 3861,
    56: 4131,
    57: 4420,
    58: 4730,
    59: 5061,
    60: 5415,
    61: 5794,
    62: 6200,
    63: 6634,
    64: 7098,
    65: 7595,
    66: 8127,
    67: 8696,
    68: 9304,
    69: 9956,
    70: 10653,
    71: 11398,
    72: 12196,
    73: 13050,
    74: 13964,
    75: 14941,
    76: 15987,
    77: 17106,
    78: 18304,
    79: 19585,
    80: 20956,
    81: 22423,
    82: 23993,
    83: 25672,
    84: 27469,
    85: 29392,
    86: 31450,
    87: 33651,
    88: 36007,
    89: 38527,
    90: 41224,
    91: 44110,
    92: 47198,
    93: 50501,
    94: 54037,
    95: 57819,
    96: 61866,
    97: 66197,
    98: 70831,
    99: 75789,
    100: 81094,
}

# Размер выборки из пула персонажей для случайного взвешенного выбора
CHARACTER_POOL_SAMPLE_SIZE: Final[int] = 100

# Начальная локация для всех новых персонажей
INITIAL_LOCATION: Final[Dict[str, str]] = {
    "current_location_id": "GATEWAY_TO_EPICENTER_1",  # Шлюз в Эпицентр-1
    "current_region_id": "1",                         # Глобальная зона "Город-Бастион"
}

# Начальные жизненные показатели
INITIAL_VITALS: Final[Dict[str, int]] = {
    "hp": 100,
    "mana": 100
}

# Начальная репутация для нового персонажа
INITIAL_REPUTATION: Final[List[Dict[str, Any]]] = [
    {"faction_id": 1, "reputation_value": 0},
    {"faction_id": 2, "reputation_value": 0},
    # ...здесь можно добавить другие стартовые фракции...
]

# Коэффициенты влияния базовых статов на производные характеристики.
STAT_MODIFIERS: Final[Dict[str, Dict[str, float]]] = {
    "strength": {
        "physical_damage_bonus": 0.0,
        "carry_weight_bonus": 0.0
    },
    "perception": {
        "accuracy_bonus": 0.0,
        "crit_chance_bonus": 0.0
    },
    "endurance": {
        "hp_per_point": 10.0,
        "stamina_per_point": 0.0
    },
    "agility": {
        "evasion_bonus": 0.0,
        "speed_bonus": 0.0
    },
    "intelligence": {
        "mana_per_point": 10.0,
        "magic_damage_bonus": 0.0
    },
    "charisma": {
        "persuasion_bonus": 0.0,
        "trade_discount_bonus": 0.0
    },
    "luck": {
        "crit_damage_bonus": 0.0,
        "loot_find_bonus": 0.0
    }
}

# --- НОВОЕ: Начальные значения для всех производных характеристик ---
INITIAL_DERIVED_STATS: Final[List[Dict[str, Any]]] = [
    {'stat_name': 'current_health', 'value': 0},
    {'stat_name': 'max_health', 'value': 0},
    {'stat_name': 'current_energy', 'value': 0},
    {'stat_name': 'crit_chance', 'value': 0},
    {'stat_name': 'crit_damage_bonus', 'value': 0},
    {'stat_name': 'anti_crit_chance', 'value': 0},
    {'stat_name': 'anti_crit_damage', 'value': 0},
    {'stat_name': 'dodge_chance', 'value': 0},
    {'stat_name': 'anti_dodge_chance', 'value': 0},
    {'stat_name': 'counter_attack_chance', 'value': 0},
    {'stat_name': 'parry_chance', 'value': 0},
    {'stat_name': 'block_chance', 'value': 0},
    {'stat_name': 'armor_penetration', 'value': 0},
    {'stat_name': 'physical_attack', 'value': 0},
    {'stat_name': 'magical_attack', 'value': 0},
    {'stat_name': 'magic_resistance', 'value': 0},
    {'stat_name': 'physical_resistance', 'value': 0},
    {'stat_name': 'mana_cost_reduction', 'value': 0},
    {'stat_name': 'regen_health_rate', 'value': 0},
    {'stat_name': 'energy_regeneration_bonus', 'value': 0},
    {'stat_name': 'energy_pool_bonus', 'value': 0},
    {'stat_name': 'absorption_bonus', 'value': 0},
    {'stat_name': 'shield_value', 'value': 0},
    {'stat_name': 'shield_regeneration', 'value': 0},
    {'stat_name': 'elemental_power_bonus', 'value': 0},
    {'stat_name': 'fire_power_bonus', 'value': 0},
    {'stat_name': 'water_power_bonus', 'value': 0},
    {'stat_name': 'air_power_bonus', 'value': 0},
    {'stat_name': 'earth_power_bonus', 'value': 0},
    {'stat_name': 'light_power_bonus', 'value': 0},
    {'stat_name': 'dark_power_bonus', 'value': 0},
    {'stat_name': 'gray_magic_power_bonus', 'value': 0},
    {'stat_name': 'fire_resistance', 'value': 0},
    {'stat_name': 'water_resistance', 'value': 0},
    {'stat_name': 'air_resistance', 'value': 0},
    {'stat_name': 'earth_resistance', 'value': 0},
    {'stat_name': 'light_resistance', 'value': 0},
    {'stat_name': 'dark_resistance', 'value': 0},
    {'stat_name': 'gray_magic_resistance', 'value': 0},
    {'stat_name': 'magic_resistance_percent', 'value': 0},
    {'stat_name': 'piercing_damage_bonus', 'value': 0},
    {'stat_name': 'slashing_damage_bonus', 'value': 0},
    {'stat_name': 'blunt_damage_bonus', 'value': 0},
    {'stat_name': 'cutting_damage_bonus', 'value': 0},
    {'stat_name': 'piercing_resistance', 'value': 0},
    {'stat_name': 'slashing_resistance', 'value': 0},
    {'stat_name': 'blunt_resistance', 'value': 0},
    {'stat_name': 'cutting_resistance', 'value': 0},
    {'stat_name': 'physical_resistance_percent', 'value': 0},
]