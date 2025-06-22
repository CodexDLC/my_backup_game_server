# -*- coding: utf-8 -*-
from typing import Dict

# ======================================================================
# --- НАСТРОЙКИ RUNTIME РЕЖИМА (КООРДИНАТОР ТИКОВ) ---
# ======================================================================

DEFAULT_BATCH_SIZE: int = 100
BATCH_SIZES: Dict[str, int] = {
    "auto_leveling": 200,
    "auto_exploring": 50
}
REDIS_TICK_BATCH_TTL: int = 3600
TICK_INTERVAL_MINUTES: int = 5

# Настройки для периодических задач ARQ Worker
PERIODIC_TASK_INTERVAL_SECONDS: int = 30 # Интервал между запусками периодической задачи (в секундах)
PERIODIC_TASK_ERROR_INTERVAL_SECONDS: int = 5 # Интервал ожидания после ошибки в периодической задаче (в секундах)