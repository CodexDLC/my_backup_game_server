# game_server\config\constants\coordinator.py
from typing import Dict

# ======================================================================
# --- КОНСТАНТЫ КООРДИНАТОРА ---
# ======================================================================

# Канал в MessageBus, который слушает Coordinator
COORDINATOR_COMMAND_QUEUE: str = "tick_coordinator_command_queue"

# --- Команды, которые приходят от Watcher'а ---
COMMAND_PROCESS_AUTO_LEVELING: str = "process_auto_leveling"
COMMAND_PROCESS_AUTO_EXPLORING: str = "process_auto_exploring"

# --- Маршрутизация задач к воркерам ---
# Имена ARQ-функций для MessageBus (для команд координатора)
ARQ_COMMAND_TASK_NAMES: Dict[str, str] = {
    "auto_leveling": "process_auto_leveling_batch",
    "auto_exploring": "process_auto_exploring_batch"
}

