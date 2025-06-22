# -*- coding: utf-8 -*-
from typing import Set, Dict, List

# --- Группы суффиксов для валидации ---
VALID_SUFFIX_GROUPS: Set[str] = {
    "ABSORPTION", "ACTIVE_DEFENSE", "ARCANE", "CRITICAL_DEFENSE", "DEBUFF",
    "ENVIRONMENTAL", "GENERAL_COMBAT", "GENERAL_DEFENSE", "MAGIC_OFFENSE",
    "PHYSICAL_DEFENSE", "PHYSICAL_OFFENSE", "SHIELDING", "SOCIAL", "STEALTH",
    "SYSTEM", "UTILITY", "VAMPIRIC", "VITALITY",
}

# --- Уровень редкости по умолчанию ---
DEFAULT_RARITY_LEVEL: int = 9

# --- Правила совместимости типов предметов и материалов ---
MATERIAL_COMPATIBILITY_RULES: Dict[str, Dict[str, List[str]]] = {
    "WEAPON": {
        "allowed_types": ["METAL", "WOOD", "BONE"],
        "disallowed_types": ["FABRIC", "LEATHER"]
    },
    "ARMOR": {
        "allowed_types": ["METAL", "LEATHER"],
        "disallowed_types": ["FABRIC"]
    },
    "APPAREL": {
        "allowed_types": ["FABRIC", "LEATHER", "FUR"],
        "disallowed_types": ["METAL"]
    },
    "ACCESSORY": {
        "allowed_types": ["METAL", "FABRIC", "LEATHER", "GEM", "BONE", "WOOD"],
        "disallowed_types": []
    },
    "UNKNOWN_CATEGORY": {
        "allowed_types": [],
        "disallowed_types": ["METAL", "FABRIC", "LEATHER"]
    }
}