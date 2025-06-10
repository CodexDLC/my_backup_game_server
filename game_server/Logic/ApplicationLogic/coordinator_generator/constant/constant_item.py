# Proposed for: game_server/Logic/ApplicationLogic/coordinator_generator/constant/item_generation_constants.py

# --- Группы суффиксов для валидации (Перенесены из generator_settings.py) ---
# Набор всех известных групп суффиксов, используемых для валидации и категоризации.
from typing import Set


VALID_SUFFIX_GROUPS: Set[str] = {
    "ABSORPTION",
    "ACTIVE_DEFENSE",
    "ARCANE",
    "CRITICAL_DEFENSE",
    "DEBUFF",
    "ENVIRONMENTAL",
    "GENERAL_COMBAT",
    "GENERAL_DEFENSE",
    "MAGIC_OFFENSE",
    "PHYSICAL_DEFENSE",
    "PHYSICAL_OFFENSE",
    "SHIELDING",
    "SOCIAL",
    "STEALTH",
    "SYSTEM",
    "UTILITY",
    "VAMPIRIC",
    "VITALITY",
}