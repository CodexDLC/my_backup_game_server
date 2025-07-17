# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/Handlers/remove_player_from_state_handler.py

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


class RemovePlayerFromStateHandler(ILocationStateHandler):
    """
    Обработчик, удаляющий ID игрока из списка 'players' в динамическом состоянии локации
    и возвращающий сводные данные.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, location_state_repo: ILocationStateRepository):
        self._logger = logger
        self._location_state_repo = location_state_repo
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, location_id: str, character_id: int) -> LocationDynamicSummaryDTO:
        """
        Удаляет персонажа из массива 'players' и обновляет 'last_update' для локации,
        затем возвращает сводные данные.

        Args:
            location_id (str): ID локации.
            character_id (int): ID персонажа, который покидает локацию.

        Returns:
            LocationDynamicSummaryDTO: Сводные данные о состоянии локации после операции.
        """
        self.logger.debug(f"Удаление персонажа {character_id} из локации {location_id}.")

        try:
            player_removed = await self._location_state_repo.remove_player_from_location(location_id, str(character_id))
            
            if not player_removed:
                self.logger.warning(f"Не удалось удалить персонажа {character_id} из локации {location_id}. Возможно, он уже не там.")

            current_time = datetime.now(timezone.utc)
            await self._location_state_repo.collection.update_one(
                {"_id": location_id},
                {"$set": {"last_update": current_time}}
            )

            updated_location_state = await self._location_state_repo.get_location_by_id(location_id)
            
            # Используем вынесенную хелпер-функцию
            summary = extract_summary_from_location_state(updated_location_state) # <--- ИСПРАВЛЕНО
            self.logger.info(f"Персонаж {character_id} удален из локации {location_id}. Текущее состояние: {summary.players_in_location} игроков, {summary.npcs_in_location} NPC.")
            
            return summary

        except Exception as e:
            self.logger.error(f"Ошибка при удалении персонажа {character_id} из локации {location_id}: {e}", exc_info=True)
            return LocationDynamicSummaryDTO() 

    # Метод _extract_summary_from_state УДАЛЕН из этого класса