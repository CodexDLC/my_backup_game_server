# game_server\Logic\ApplicationLogic\auth_service\ShardManagement\Handlers\i_shard_management_handler.py

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any

class IShardManagementHandler(ABC):
    """
    Абстрактный класс для одного из обработчиков в процессе управления шардами.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        self.dependencies = dependencies
        self.logger = dependencies.get('logger', logging.getLogger(self.__class__.__name__))

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """
        Выполняет основную логику обработчика.
        """
        pass