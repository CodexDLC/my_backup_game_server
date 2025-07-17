# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/Handlers/i_location_state_handler.py

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict
from game_server.contracts.dtos.game_commands.data_models import LocationDynamicSummaryDTO # Импортируем наш DTO


class ILocationStateHandler(ABC):
    """
    Абстрактный базовый класс для обработчиков, управляющих динамическим состоянием локации.
    Определяет общий контракт для операций с состоянием локации.
    """
    @property
    @abstractmethod
    def logger(self) -> logging.Logger:
        """Возвращает экземпляр логгера для обработчика."""
        pass

    @abstractmethod
    async def process(self, **kwargs: Any) -> LocationDynamicSummaryDTO: # Возвращает наш DTO
        """
        Абстрактный метод, выполняющий основную бизнес-логику обработчика состояния локации.
        Принимает необходимые аргументы через kwargs.
        Должен быть реализован в дочерних классах.
        Возвращает LocationDynamicSummaryDTO.
        """
        pass