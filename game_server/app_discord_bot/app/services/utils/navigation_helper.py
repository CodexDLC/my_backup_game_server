# game_server/app_discord_bot/app/services/utils/navigation_helper.py

import inject
import discord
import logging
import json
from typing import Dict, Any

from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

class NavigationHelper:
    """
    Хелпер для инкапсуляции общей логики, связанной с навигацией.
    """
    @inject.autoparams()
    def __init__(
        self,
        character_cache_manager: ICharacterCacheManager,
        account_data_manager: IAccountDataManager,
        logger: logging.Logger,
    ):
        self.character_cache_manager = character_cache_manager
        self.account_data_manager = account_data_manager
        self.logger = logger

    async def get_current_location_details_for_user(self, user: discord.User) -> Dict[str, Any]:
        """
        Получает детали текущей локации для указанного пользователя.

        1. Находит активного персонажа пользователя.
        2. Определяет его current_location_id из кэша сессии.
        3. Загружает и возвращает полные данные о локации из глобального кэша мира.
        
        Args:
            user (discord.User): Пользователь, для которого нужно найти локацию.

        Returns:
            Dict[str, Any]: Словарь с деталями текущей локации.
        
        Raises:
            ValueError: Если какой-либо из шагов не удался.
        """
        self.logger.debug(f"Запрос деталей текущей локации для пользователя {user.name}")

        # 1. Получаем ID активного персонажа
        character_id = await self.character_cache_manager.get_active_character_id(user.id)
        if not character_id:
            raise ValueError(f"Не найдена активная сессия персонажа для пользователя {user.id}.")

        # 2. Получаем ID локации из сессии персонажа
        character_session = await self.character_cache_manager.get_character_session(character_id, user.guild.id)
        if not character_session:
            raise ValueError(f"Не найден кэш для сессии персонажа {character_id}.")
        
        location_block = character_session.get("location", {})
        current_location_info = location_block.get("current", {})
        location_id = current_location_info.get("location_id")

        if not location_id:
            raise ValueError("Ключ 'location.current.location_id' не найден в кэше сессии.")
        
        # 3. Получаем статические данные о локации
        location_details_json = await self.account_data_manager.get_hash_field(
            RedisKeys.GLOBAL_GAME_WORLD_DATA, str(location_id)
        )
        if not location_details_json:
            raise ValueError(f"Детали для локации ID {location_id} не найдены в глобальных данных мира.")
            
        return json.loads(location_details_json)