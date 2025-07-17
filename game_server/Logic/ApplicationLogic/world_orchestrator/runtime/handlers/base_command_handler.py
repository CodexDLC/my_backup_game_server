# =================================================================================
# Файл: /game_server/Logic/ApplicationLogic/world_orchestrator/runtime/handlers/base_command_handler.py
# =================================================================================
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging # Добавлено для типизации логгера
import inject # Добавлено для inject.attr

class ICommandHandler(ABC):
    """Абстрактный интерфейс для всех обработчиков команд в реальном времени."""
    # 🔥 ИЗМЕНЕНИЕ: Логгер теперь внедряется как атрибут класса через inject
    logger: logging.Logger = inject.attr(logging.Logger)

    # 🔥 ИЗМЕНЕНИЕ: Удален конструктор, так как зависимости будут внедряться напрямую в наследниках
    # def __init__(self, dependencies: Dict[str, Any]):
    #     self.dependencies = dependencies
    #     self.logger = dependencies.get("logger")

    @abstractmethod
    async def execute(self, payload: Dict[str, Any]):
        """Основной метод, который выполняет бизнес-логику команды."""
        pass