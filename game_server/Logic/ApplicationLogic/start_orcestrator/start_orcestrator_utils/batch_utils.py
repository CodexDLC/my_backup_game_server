# game_server/Logic/ApplicationLogic/start_orcestrator/start_orcestrator_utils/batch_utils.py
# import uuid # Больше не нужен, если uuid генерируется в TaskQueueCacheManager
# import json # Больше не нужен
from typing import List, Dict, Any, Iterator

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger



def split_into_batches(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
    """Разбивает список на батчи указанного размера."""
    if not data or batch_size <= 0:
        return iter([])
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

