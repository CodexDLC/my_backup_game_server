# game_server/Logic/ApplicationLogic/shared_logic/ShardManagement/Handlers/i_shard_management_handler.py

from abc import ABC, abstractmethod
from typing import Any, Dict

# 🔥 ИЗМЕНЕНО: Удалены зависимости из __init__
# class IShardManagementHandler(ABC):
#    """
#    Абстрактный класс для одного из обработчиков в процессе управления шардами.
#    """
#    def __init__(self, dependencies: Dict[str, Any]): # УДАЛЕНО
#        self.dependencies = dependencies # УДАЛЕНО
#        self.logger = dependencies.get('logger', logging.getLogger(self.__class__.__name__)) # УДАЛЕНО

class IShardManagementHandler(ABC):
    """
    Абстрактный класс для одного из обработчиков в процессе управления шардами.
    Теперь зависимости будут внедряться напрямую в наследниках через @inject.autoparams.
    """
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """
        Выполняет основную логику обработчика.
        """
        pass