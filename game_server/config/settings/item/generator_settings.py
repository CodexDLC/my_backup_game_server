# -*- coding: utf-8 -*-
from typing import Dict, Any

# --- Настройки редкости предметов ---
# Определяет, на какие "тиры ценности" может претендовать предмет
# в зависимости от его уровня редкости (1-9), а также вероятности
# выпадения каждого из доступных тиров.
ITEM_RARITY_TIER_MAPPING: Dict[int, Dict[str, Any]] = {
    # Rarity Level: {min_tier, max_tier, probabilities}
    1: {"min_possible_tier": 1, "max_possible_tier": 1, "tier_roll_bias": [1.0]},        # Basic
    2: {"min_possible_tier": 1, "max_possible_tier": 2, "tier_roll_bias": [0.6, 0.4]},     # Common
    3: {"min_possible_tier": 2, "max_possible_tier": 3, "tier_roll_bias": [0.7, 0.3]},     # Uncommon
    4: {"min_possible_tier": 2, "max_possible_tier": 4, "tier_roll_bias": [0.3, 0.4, 0.3]}, # Rare
    5: {"min_possible_tier": 3, "max_possible_tier": 5, "tier_roll_bias": [0.2, 0.4, 0.4]}, # Epic
    6: {"min_possible_tier": 4, "max_possible_tier": 6, "tier_roll_bias": [0.1, 0.3, 0.6]}, # Legendary
    7: {"min_possible_tier": 5, "max_possible_tier": 6, "tier_roll_bias": [0.3, 0.7]},     # Mythical
    8: {"min_possible_tier": 6, "max_possible_tier": 6, "tier_roll_bias": [1.0]},        # Divine
    9: {"min_possible_tier": 1, "max_possible_tier": 1, "tier_roll_bias": [1.0]}         # No-rarity / Junk
}