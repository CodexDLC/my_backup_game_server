# game_server/Logic/ApplicationLogic/SystemServices/handler/i_system_handler.py

from abc import ABC, abstractmethod
import logging
from typing import Any

class ISystemServiceHandler(ABC):
    """
    Абстрактный базовый класс для обработчиков команд в микросервисе SystemServices.
    Определяет общий контракт для инициализации и выполнения бизнес-логики.
    """
    @property
    @abstractmethod
    def logger(self) -> logging.Logger:
        """Возвращает экземпляр логгера для обработчика."""
        pass

    @abstractmethod
    async def process(self, command_dto: Any) -> Any:
        """
        Абстрактный метод, выполняющий основную бизнес-логику обработчика.
        Должен быть реализован в дочерних классах.
        Принимает DTO команды.
        """
        pass