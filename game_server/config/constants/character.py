# game_server\config\constants\character.py
from typing import Dict, Any, List, Set

# ======================================================================
# --- БАЗОВЫЕ КОНСТАНТЫ ГЕНЕРАЦИИ ПЕРСОНАЖЕЙ ---
# ======================================================================

# --- Общая конфигурация для всех бросков кубиков ---
BASE_ROLL_CONFIG: Dict[str, int] = {
    "num_rolls": 3,
    "dice_type": 6,
    "drop_lowest": 0,
}

# --- Список всех 7 основных характеристик персонажа ---
SPECIAL_STATS: List[str] = [
    "STRENGTH",      # S
    "PERCEPTION",    # P
    "ENDURANCE",     # E
    "CHARISMA",      # C
    "INTELLIGENCE",  # I
    "AGILITY",       # A
    "LUCK"           # L
]

# --- Определение групп навыков и их ограничений ---
SKILL_GROUP_LIMITS: Dict[str, Dict[str, Any]] = {
    "magic_elemental": {"limit_type": "exclusive", "limit_value": 1},
    "combat_weapon": {"limit_type": "exclusive", "limit_value": 1},
    "armor_type_proficiency": {"limit_type": "exclusive", "limit_value": 1},
    "shield_proficiency": {"limit_type": "exclusive", "limit_value": 1},
    "tactical_core_combat": {"limit_type": "any", "limit_value": 2},
    "tactical_resilience": {"limit_type": "any", "limit_value": 1},
    "magic_special": {"limit_type": "exclusive", "limit_value": 1},
    "gathering_utility": {"limit_type": "any", "limit_value": 3},
    "gathering_combat": {"limit_type": "exclusive", "limit_value": 1},
    "crafting_production": {"limit_type": "any", "limit_value": 2},
    "social_cooperation_orientation": {"limit_type": "exclusive", "limit_value": 1},
}

# --- Архетипы NPC ---
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

# --- Роли NPC ---
NPC_ROLES: Dict[str, Dict[str, Any]] = {
    "TRADER": {
        "weight": 0.10,
        "skill_preference_tags": {"limit_groups": [], "specific_skills": ["trader", "negotiator"]},
        "description": "Специализируется на торговле и экономических операциях.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["CHARISMA", "INTELLIGENCE", "LUCK"]
    },
    "CRAFTER": {
        "weight": 0.08,
        "skill_preference_tags": {"limit_groups": ["crafting_production"], "specific_skills": ["weaponsmith", "armorsmith"]},
        "description": "Занимается созданием и ремонтом предметов, с упором на оружие и броню.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["INTELLIGENCE", "AGILITY", "PERCEPTION"]
    },
    "GATHERER": {
        "weight": 0.10,
        "skill_preference_tags": {"limit_groups": ["gathering_utility"], "specific_skills": ["forager", "herbalist"]},
        "description": "Собирает природные ресурсы и выживает в дикой местности.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["PERCEPTION", "ENDURANCE", "LUCK"]
    },
    "WARRIOR": {
        "weight": 0.20,
        "skill_preference_tags": {"limit_groups": ["combat_weapon", "armor_type_proficiency"], "specific_skills": ["slashing_weapon_user", "heavy_armor_user"]},
        "description": "Мастер ближнего боя и защиты, предпочитающий тяжелую броню.",
        "archetype_affinity": ["COMBAT_FOCUSED"],
        "stat_priority": ["STRENGTH", "ENDURANCE", "AGILITY"]
    },
    "RANGER": {
        "weight": 0.15,
        "skill_preference_tags": {"limit_groups": ["combat_weapon", "gathering_combat"], "specific_skills": ["ranged_master", "hunter"]},
        "description": "Специалист по дальнему бою, скрытности и выживанию в дикой местности.",
        "archetype_affinity": ["COMBAT_FOCUSED"],
        "stat_priority": ["PERCEPTION", "AGILITY", "ENDURANCE"]
    },
    "HEALER": {
        "weight": 0.07,
        "skill_preference_tags": {"limit_groups": [], "specific_skills": ["healer", "light_mage"]},
        "description": "Использует целительские и поддерживающие навыки, включая магию света.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["CHARISMA", "INTELLIGENCE", "PERCEPTION"]
    },
    "ELEMENTALIST": {
        "weight": 0.07,
        "skill_preference_tags": {"limit_groups": ["magic_elemental", "armor_type_proficiency"], "specific_skills": ["pyromancer", "light_armor_user"]},
        "description": "Владеет силами природы и стихийной магией, предпочитая легкую броню.",
        "archetype_affinity": ["COMBAT_FOCUSED"],
        "stat_priority": ["INTELLIGENCE", "PERCEPTION", "AGILITY"]
    },
    "SCHOLAR": {
        "weight": 0.08,
        "skill_preference_tags": {"limit_groups": [], "specific_skills": ["scientist", "arcane_scholar"]},
        "description": "Посвящает себя изучению мира, знаний и магии.",
        "archetype_affinity": ["PEACEFUL_FOCUSED"],
        "stat_priority": ["INTELLIGENCE", "PERCEPTION", "CHARISMA"]
    },
    "LEADER": {
        "weight": 0.08,
        "skill_preference_tags": {"limit_groups": ["social_cooperation_orientation"], "specific_skills": ["leader", "negotiator", "organizer", "team_player"]},
        "description": "Обладает навыками управления, убеждения и организации других.",
        "archetype_affinity": ["COMBAT_FOCUSED", "PEACEFUL_FOCUSED"],
        "stat_priority": ["CHARISMA", "INTELLIGENCE", "LUCK"]
    }
}


# ======================================================================
# --- ПРОИЗВОДНЫЕ КОНСТАНТЫ (из бывшего constant_Cha.py) ---
# ======================================================================
# Эти константы вычисляются на основе NPC_ROLES для удобства использования в коде.

# Мирные роли
PEACEFUL_ROLES: Set[str] = {
    role_name
    for role_name, role_data in NPC_ROLES.items()
    if "PEACEFUL_FOCUSED" in role_data.get("archetype_affinity", []) and
       "COMBAT_FOCUSED" not in role_data.get("archetype_affinity", [])
}

# Боевые роли
COMBAT_ROLES: Set[str] = {
    role_name
    for role_name, role_data in NPC_ROLES.items()
    if "COMBAT_FOCUSED" in role_data.get("archetype_affinity", [])
}

# Сопоставление ролей с их архетипами
ROLE_ARCHETYPE_AFFINITY: Dict[str, Set[str]] = {
    role_name: set(role_data.get("archetype_affinity", []))
    for role_name, role_data in NPC_ROLES.items()
}


# ======================================================================
# --- КОНСТАНТЫ ПРОЦЕССА ГЕНЕРАЦИИ ПЕРСОНАЖЕЙ ---
# ======================================================================

# Имя очереди для задач по генерации персонажей
CHARACTER_GENERATION_WORKER_QUEUE_NAME: str = "character_generation_worker_queue"

# Название уровня качества, считающегося наивысшим
HIGHEST_QUALITY_LEVEL_NAME: str = "SUPERIOR_ELITE_QUALITY"

# --- ID по умолчанию для атрибутов персонажа ---
DEFAULT_PERSONALITY_ID: int = 1
DEFAULT_BACKGROUND_STORY_ID: int = 1
DEFAULT_STARTER_INVENTORY_ID: int = 100