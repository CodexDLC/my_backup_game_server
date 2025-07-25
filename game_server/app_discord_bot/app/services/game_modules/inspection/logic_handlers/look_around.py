# game_server/app_discord_bot/app/services/game_modules/inspection/logic_handlers/look_around_overview.py

import discord
import inject
import logging
import json
from typing import Dict, Any, Optional, List

# Импортируем наши DTO и интерфейсы менеджеров
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import LookAroundResultDTO, LookAroundResultObjectDTO
from game_server.app_discord_bot.app.services.game_modules.inspection.category_registry import CATEGORY_REGISTRY
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheDiscordManager
from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager

class LookAroundOverviewHandler:
    """
    Обрабатывает команду 'look_around'.
    Собирает сводную информацию о содержимом локации из Redis
    и передает ее для отображения общего обзора.
    """
    @inject.autoparams()
    def __init__(
        self, 
        logger: logging.Logger, 
        account_data_manager: IAccountDataManager,
        character_cache_manager: ICharacterCacheDiscordManager,
        game_world_data_manager: IGameWorldDataManager
    ):
        self.logger = logger
        self.account_data_manager = account_data_manager
        self.character_cache_manager = character_cache_manager
        self.game_world_data_manager = game_world_data_manager
        
        # Соответствие ключей из Redis-хеша локации ключам категорий в нашем приложении
        self.redis_to_category_map = {
            "players_in_location": "players",
            "npcs_in_location": "npc_neutral" # Пример, может потребоваться уточнение
            # Добавьте сюда другие соответствия, когда они понадобятся
        }
        
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self, command_str: str, interaction: discord.Interaction) -> Optional[LookAroundResultDTO]:
        """
        Основной метод выполнения логики.
        """
        self.logger.info(f"Обработка команды '{command_str}' для пользователя {interaction.user.id}")

        try:
            # --- Шаг 1: Получение ID активного персонажа ---
            active_session = await self.account_data_manager.get_active_session(interaction.user.id)
            if not active_session or "character_id" not in active_session:
                self.logger.warning(f"Не найдена активная сессия для пользователя {interaction.user.id}")
                # TODO: Отправить пользователю сообщение о том, что нужно войти в игру
                return None
            
            character_id = active_session["character_id"]
            guild_id = interaction.guild_id

            # --- Шаг 2: Получение данных сессии персонажа, чтобы узнать его локацию ---
            char_session_data = await self.character_cache_manager.get_character_session(character_id, guild_id)
            if not char_session_data or "location" not in char_session_data:
                self.logger.error(f"Не удалось получить данные сессии и ли локацию для персонажа {character_id}")
                return None
            
            # Парсим JSON-строку с информацией о локации
            location_data = char_session_data["location"]
            current_location_id = location_data.get("current", {}).get("location_id")

            if not current_location_id:
                self.logger.error(f"В данных сессии персонажа {character_id} отсутствует current.location_id")
                return None

            # --- Шаг 3: Получение сводных данных о локации из Redis ---
            location_key = f"global:game_world_data_dynamic:{current_location_id}"
            dynamic_summary_data = await self.game_world_data_manager.get_all_hash_fields(location_key)
            
            if not dynamic_summary_data:
                self.logger.info(f"Нет динамических данных для локации {current_location_id}")
                return None

            self.logger.debug(f"Получены динамические данные для локации {current_location_id}: {dynamic_summary_data}")

            # --- Шаг 4: Обработка полученных данных и формирование DTO ---
            dynamic_entities_list: List[LookAroundResultObjectDTO] = []
            environmental_objects_list: List[LookAroundResultObjectDTO] = []

            for redis_key, count_str in dynamic_summary_data.items():
                category_key = self.redis_to_category_map.get(redis_key)
                if not category_key:
                    continue # Игнорируем ключи, для которых нет соответствия

                try:
                    count = int(count_str)
                except (ValueError, TypeError):
                    self.logger.warning(f"Не удалось преобразовать в число значение '{count_str}' для ключа '{redis_key}'")
                    continue
                
                if category_key in CATEGORY_REGISTRY and count > 0:
                    registry_info = CATEGORY_REGISTRY[category_key]
                    obj_dto = LookAroundResultObjectDTO(
                        category_key=category_key,
                        display_name=registry_info["display_name"],
                        count=count,
                        description_key=registry_info["description_key"],
                        embed_group=registry_info["embed_group"]
                    )
                    if registry_info["embed_group"] == "dynamic_entities":
                        dynamic_entities_list.append(obj_dto)
                    elif registry_info["embed_group"] == "environmental_objects":
                        environmental_objects_list.append(obj_dto)

            if not dynamic_entities_list and not environmental_objects_list:
                self.logger.info(f"В локации {current_location_id} не найдено ничего интересного для осмотра.")
                return None 

            return LookAroundResultDTO(
                dynamic_entities=dynamic_entities_list,
                environmental_objects=environmental_objects_list
            )
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при выполнении команды 'look_around': {e}", exc_info=True)
            return None # В случае любой ошибки возвращаем None