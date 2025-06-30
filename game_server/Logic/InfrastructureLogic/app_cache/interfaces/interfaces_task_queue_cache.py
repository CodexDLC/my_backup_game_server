# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_task_queue_cache.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ITaskQueueCacheManager(ABC):
    """
    Интерфейс для менеджера кэша очереди задач.
    Определяет методы, необходимые для взаимодействия с Redis для хранения
    и управления спецификациями задач для ARQ-воркеров.
    """

    @abstractmethod
    async def add_task_to_queue(
        self,
        batch_id: str,
        key_template: str,
        specs: List[Dict[str, Any]],
        target_count: int,
        initial_status: str,
        ttl_seconds: Optional[int] = None # Добавляем TTL, если нужно гибко управлять им
    ) -> bool:
        """
        Добавляет батч спецификаций задачи в Redis для последующей обработки.
        """
        pass

    @abstractmethod
    async def get_task_batch_specs(
        self,
        batch_id: str,
        key_template: str,
        log_prefix: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Извлекает спецификации батча задачи из Redis.
        """
        pass

    @abstractmethod
    async def update_task_status(
        self,
        batch_id: str,
        key_template: str,
        status: str,
        log_prefix: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Обновляет статус задачи в Redis.
        """
        pass