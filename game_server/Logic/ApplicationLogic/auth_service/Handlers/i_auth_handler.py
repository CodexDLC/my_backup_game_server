# game_server/Logic/ApplicationLogic/auth_service/Handlers/i_auth_handler.py

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any

class IAuthHandler(ABC):
    """
    Абстрактный класс для одного из обработчиков в процессе аутентификации.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        self.dependencies = dependencies
        self.logger = dependencies.get('logger', logging.getLogger(self.__class__.__name__))

    @abstractmethod
    async def process(self, dto: Any) -> Any:
        """ Выполняет логику обработчика и возвращает внутренний DTO с результатом. """
        pass