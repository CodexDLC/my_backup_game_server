# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_dinamic_location_manager.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IDynamicLocationManager(ABC):
    """
    Интерфейс для сервиса, управляющего кэшем
    динамических сводных данных о локациях в Redis.
    """

    @abstractmethod
    async def update_location_summary(self, location_id: str, summary_data: Dict[str, Any]) -> None:
        """
        Обновляет (перезаписывает) хэш с сводными данными для указанной локации.
        """
        pass

    @abstractmethod
    async def get_location_summary(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает хэш с сводными данными для указанной локации.
        Возвращает словарь в случае успеха или None, если ключ не найден.
        """
        pass