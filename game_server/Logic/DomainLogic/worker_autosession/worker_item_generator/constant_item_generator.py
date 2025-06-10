ITEM_RARITY_TIER_MAPPING = {
    # Здесь используются 6 value_tiers как в предыдущем примере (1% - 10%)
    1: {"min_possible_tier": 1, "max_possible_tier": 1, "tier_roll_bias": [1.0]}, # Basic: Only value_tier 1 (e.g. 1%)
    2: {"min_possible_tier": 1, "max_possible_tier": 2, "tier_roll_bias": [0.6, 0.4]}, # Common: value_tier 1-2
    3: {"min_possible_tier": 2, "max_possible_tier": 3, "tier_roll_bias": [0.7, 0.3]}, # Uncommon: value_tier 2-3
    4: {"min_possible_tier": 2, "max_possible_tier": 4, "tier_roll_bias": [0.3, 0.4, 0.3]}, # Rare: value_tier 2-4
    5: {"min_possible_tier": 3, "max_possible_tier": 5, "tier_roll_bias": [0.2, 0.4, 0.4]}, # Epic: value_tier 3-5
    6: {"min_possible_tier": 4, "max_possible_tier": 6, "tier_roll_bias": [0.1, 0.3, 0.6]}, # Legendary: value_tier 4-6
    7: {"min_possible_tier": 5, "max_possible_tier": 6, "tier_roll_bias": [0.3, 0.7]}, # Mythical: value_tier 5-6 (Very high chance for max tier)
    8: {"min_possible_tier": 6, "max_possible_tier": 6, "tier_roll_bias": [1.0]}, # Divine: Guaranteed highest tier (value_tier 6)
    9: {"min_possible_tier": 1, "max_possible_tier": 1, "tier_roll_bias": [1.0]} # No-rarity / Junk items (always value_tier 1)
}

