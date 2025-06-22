# -*- coding: utf-8 -*-
from typing import Dict, Optional

# ======================================================================
# --- НАСТРОЙКИ ПРЕДСТАРТОВОГО РЕЖИМА (ГЕНЕРАТОРЫ) ---
# ======================================================================

# --- Общие ---
MAX_TASK_RETRY_ATTEMPTS: int = 3

# --- Генератор Персонажей ---
CHARACTER_POOL_TARGET_SIZE: int = 5000
CHARACTER_GENERATION_MAX_BATCH_SIZE: int = 500
DEFAULT_CHARACTER_GENDER_RATIO: float = 0.5

# --- Генератор Предметов ---
ITEM_GENERATION_LIMIT: Optional[int] = None
ITEM_GENERATION_BATCH_SIZE: int = 500
ETALON_POOL_TTL_SECONDS: int = 1800
DEFAULT_WEIGHT_FOR_MISSING_RARITY: int = 100
BASE_ROLL_RARITY_MODIFIER: Dict[int, int] = {
    1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2,
}

# Настройка размера батча для удаления сидов
SEEDING_DELETION_BATCH_SIZE: int = 50