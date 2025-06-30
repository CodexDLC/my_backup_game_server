# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_run/coordinator_handler/base_handler.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class ICommandHandler(ABC):
    """
    Абстрактный интерфейс для всех обработчиков команд Координатора.
    Гарантирует, что каждый обработчик будет иметь метод execute.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        """
        Конструктор принимает словарь с общими зависимостями (клиенты, менеджеры).
        """
        self.dependencies = dependencies
        self.logger = dependencies.get("logger")
        # Здесь можно для удобства сразу извлечь часто используемые зависимости
        # self.repository_manager = dependencies.get("repository_manager")
        # self.arq_redis_client = dependencies.get("arq_redis_client")

    @abstractmethod
    async def execute(self, command_dto: Any):
        """
        Основной метод, который выполняет бизнес-логику команды.
        Должен быть реализован в каждом конкретном обработчике.

        Args:
            command_dto: Валидированный Pydantic DTO объект с данными команды.
        """
        pass