# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/Handlers/add_player_to_state_handler.py

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

# from game_server.utils.transactional_decorator import transactional


class AddPlayerToStateHandler(ILocationStateHandler):
    """
    Обработчик, добавляющий ID игрока в список 'players' в динамическом состоянии локации
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
        Добавляет персонажа в массив 'players' и обновляет 'last_update' для локации,
        затем возвращает сводные данные.

        Args:
            location_id (str): ID локации.
            character_id (int): ID персонажа, который входит в локацию.

        Returns:
            LocationDynamicSummaryDTO: Сводные данные о состоянии локации после операции.
        """
        self.logger.debug(f"Добавление персонажа {character_id} в локацию {location_id}.")

        player_data = {"player_id": str(character_id)}
        
        try:
            player_added = await self._location_state_repo.add_player_to_location(location_id, player_data)
            
            if not player_added:
                self.logger.warning(f"Не удалось добавить персонажа {character_id} в локацию {location_id}. Возможно, он уже там.")

            # Явно обновляем last_update, так как add_player_to_location только добавляет в массив.
            current_time = datetime.now(timezone.utc)
            # MongoDB может хранить datetime объекты напрямую,
            # но если ожидается $date формат, то: {"$date": current_time.isoformat().replace('+00:00', 'Z')}
            await self._location_state_repo.collection.update_one(
                {"_id": location_id},
                {"$set": {"last_update": current_time}} # Сохраняем как datetime, чтобы Mongo сам преобразовал в ISODate
            )

            # Получаем обновленное состояние локации, чтобы собрать сводку
            updated_location_state = await self._location_state_repo.get_location_by_id(location_id)
            
            # Используем вынесенную хелпер-функцию
            summary = extract_summary_from_location_state(updated_location_state) # <--- ИСПРАВЛЕНО
            self.logger.info(f"Персонаж {character_id} добавлен в локацию {location_id}. Текущее состояние: {summary.players_in_location} игроков, {summary.npcs_in_location} NPC.")
            
            return summary

        except Exception as e:
            self.logger.error(f"Ошибка при добавлении персонажа {character_id} в локацию {location_id}: {e}", exc_info=True)
            return LocationDynamicSummaryDTO() 

    # Метод _extract_summary_from_state УДАЛЕН из этого класса и перенесен в location_state_helpers.py