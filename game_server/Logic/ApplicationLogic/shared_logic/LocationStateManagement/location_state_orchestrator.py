# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/location_state_orchestrator.py

import inject
import logging
from typing import Dict, Any, Optional

from game_server.contracts.dtos.game_commands.data_models import LocationDynamicSummaryDTO

from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.add_player_to_state_handler import AddPlayerToStateHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.remove_player_from_state_handler import RemovePlayerFromStateHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.get_location_summary_handler import GetLocationSummaryHandler


class LocationStateOrchestrator:
    """
    Оркестратор для управления динамическим состоянием локаций (на бэкенде).
    Предоставляет высокоуровневые методы, которые делегируют выполнение
    специализированным обработчикам.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        add_player_handler: AddPlayerToStateHandler,
        remove_player_handler: RemovePlayerFromStateHandler,
        get_summary_handler: GetLocationSummaryHandler,
    ):
        self.logger = logger
        self._add_player_handler = add_player_handler
        self._remove_player_handler = remove_player_handler
        self._get_summary_handler = get_summary_handler
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    # 🔥🔥 ВОТ ЭТОТ МЕТОД ДОЛЖЕН БЫТЬ В ЭТОМ ФАЙЛЕ 🔥🔥
    async def update_player_location_state_and_get_summary(
        self,
        old_location_id: Optional[str],
        new_location_id: str,
        character_id: int
    ) -> LocationDynamicSummaryDTO:
        """
        Обновляет состояние игрока в локациях (удаляет из старой, добавляет в новую)
        и возвращает сводные данные о новой локации.

        Args:
            old_location_id (Optional[str]): ID старой локации персонажа. None, если персонаж только входит в мир.
            new_location_id (str): ID новой локации персонажа.
            character_id (int): ID перемещающегося персонажа.

        Returns:
            LocationDynamicSummaryDTO: Сводные данные о состоянии новой локации.
        """
        self.logger.debug(f"Обновление состояния игрока {character_id}: из {old_location_id} в {new_location_id}.")

        # 1. Удаляем игрока из старой локации (если она была)
        if old_location_id:
            await self._remove_player_handler.process(location_id=old_location_id, character_id=character_id)
            self.logger.debug(f"Персонаж {character_id} удален из старой локации {old_location_id}.")
        else:
            self.logger.debug(f"Персонаж {character_id} не был в старой локации (old_location_id is None).")

        # 2. Добавляем игрока в новую локацию
        summary = await self._add_player_handler.process(location_id=new_location_id, character_id=character_id)
        self.logger.debug(f"Персонаж {character_id} добавлен в новую локацию {new_location_id}. Summary: {summary}.")

        return summary

    async def get_location_summary(self, location_id: str) -> LocationDynamicSummaryDTO:
        """
        Получает сводные данные о динамическом состоянии указанной локации.
        Используется для таких функций, как "осмотреться".

        Args:
            location_id (str): ID локации.

        Returns:
            LocationDynamicSummaryDTO: Сводные данные о состоянии локации.
        """
        self.logger.debug(f"Запрос сводных данных для локации {location_id} через оркестратор.")
        summary = await self._get_summary_handler.process(location_id=location_id)
        return summary