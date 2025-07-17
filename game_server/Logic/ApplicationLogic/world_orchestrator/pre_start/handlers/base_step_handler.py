# game_server/Logic/ApplicationLogic/world_orchestrator/pre_start/handlers/base_step_handler.py
from abc import ABC, abstractmethod
import logging
import inject

class IPreStartStepHandler(ABC):
    """Абстрактный класс для одного шага в процессе предстартовой генерации."""
    # Логгер теперь внедряется как атрибут класса через inject
    logger: logging.Logger = inject.attr(logging.Logger)

    @abstractmethod
    async def execute(self) -> bool:
        """Выполняет логику шага и возвращает True в случае успеха, иначе False."""
        pass
