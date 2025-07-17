# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/Handlers/get_location_summary_handler.py

import logging
import inject
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Корректный импорт ILocationStateHandler
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.Handlers.i_location_state_handler import ILocationStateHandler
# Корректный импорт ILocationStateRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository # <--- ИСПРАВЛЕНО
# Импорт DTO
from game_server.contracts.dtos.game_commands.data_models import LocationDynamicSummaryDTO
# Импорт новой хелпер-функции
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.location_state_helpers import extract_summary_from_location_state # <--- НОВОЕ


class GetLocationSummaryHandler(ILocationStateHandler):
    """
    Обработчик, получающий сводные данные о динамическом состоянии локации
    без изменения ее содержимого. Используется для команды "осмотреться".
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, location_state_repo: ILocationStateRepository):
        self._logger = logger
        self._location_state_repo = location_state_repo
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, location_id: str) -> LocationDynamicSummaryDTO:
        """
        Получает текущее состояние локации и возвращает сводные данные о ней.

        Args:
            location_id (str): ID локации, для которой нужно получить сводку.

        Returns:
            LocationDynamicSummaryDTO: Сводные данные о состоянии локации.
        """
        self.logger.debug(f"Запрос сводных данных для локации {location_id}.")

        try:
            location_state = await self._location_state_repo.get_location_by_id(location_id)
            
            # Используем вынесенную хелпер-функцию
            summary = extract_summary_from_location_state(location_state) # <--- ИСПРАВЛЕНО
            self.logger.info(f"Сводные данные для локации {location_id} получены: {summary.players_in_location} игроков, {summary.npcs_in_location} NPC.")
            
            return summary

        except Exception as e:
            self.logger.error(f"Ошибка при получении сводных данных для локации {location_id}: {e}", exc_info=True)
            return LocationDynamicSummaryDTO() 

    # Метод _extract_summary_from_state УДАЛЕН из этого класса