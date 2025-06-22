from abc import ABC, abstractmethod
import logging # Убедимся, что logging импортирован, если logger используется напрямую

class IPreStartStepHandler(ABC):
    """
    Абстрактный класс для одного шага в процессе предстартовой генерации.
    """
    def __init__(self, coordinator_dependencies: dict):
        # Принимает словарь с зависимостями от координатора
        self.dependencies = coordinator_dependencies
        # Убедитесь, что 'logger' всегда присутствует в зависимостях
        self.logger = coordinator_dependencies.get('logger', logging.getLogger(__name__))

    @abstractmethod
    async def execute(self) -> bool:
        """
        Выполняет логику шага и возвращает True в случае успеха, иначе False.
        """
        pass