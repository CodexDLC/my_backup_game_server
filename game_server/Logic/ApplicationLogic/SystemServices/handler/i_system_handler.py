# game_server/Logic/ApplicationLogic/SystemServices/handler/i_system_handler.py

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any

class ISystemServiceHandler(ABC):
    """
    Абстрактный базовый класс для обработчиков команд в микросервисе SystemServices.
    Определяет общий контракт для инициализации и выполнения бизнес-логики.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализирует обработчик с необходимыми зависимостями.
        :param dependencies: Словарь с зависимостями, предоставленными оркестратором.
        """
        self.dependencies = dependencies
        # Использование логгера из зависимостей, или создание нового, если не предоставлен
        self.logger = dependencies.get('logger', logging.getLogger(self.__class__.__name__))
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """
        Абстрактный метод, выполняющий основную бизнес-логику обработчика.
        Должен быть реализован в дочерних классах.
        Принимает произвольные аргументы, чтобы быть гибким для разных команд.
        """
        pass

