from abc import ABC, abstractmethod
from typing import Dict, Any

class ICommandHandler(ABC):
    """
    Абстрактный базовый класс (интерфейс) для всех обработчиков команд.
    Определяет единый метод `execute`, который должны реализовать все конкретные обработчики.
    
    Этот класс не содержит логики, а только определяет "контракт" (правила),
    которым должны следовать другие классы.
    """
    @abstractmethod
    async def execute(self, payload: Dict[str, Any]) -> None:
        """
        Основной метод, выполняющий всю логику, связанную с командой.
        
        Args:
            payload (Dict[str, Any]): Полезная нагрузка из сообщения, 
                                      содержащая команду и ее данные.
        """
        pass