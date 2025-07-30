# game_server/app_discord_bot/app/services/navigation/logic_handlers/show_navigation.py

import inject
import discord
import logging
from typing import Dict, Any, List

# Импортируем наш новый словарь с описаниями
from game_server.app_discord_bot.config.assets.descriptions_text.location_descriptions import LOCATION_DESCRIPTIONS

# Менеджеры кэша
from game_server.app_discord_bot.app.services.game_modules.navigation.dtos import NavigationDisplayDataDTO
from game_server.app_discord_bot.app.services.utils.navigation_helper import NavigationHelper
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheDiscordManager # Импортируем для доступа к сессии персонажа

class ShowNavigationHandler:
    """
    Логический обработчик для команды 'show_navigation'.
    Получает данные о текущей локации и подготавливает их для презентации.
    """
    @inject.autoparams()
    def __init__(self, navigation_helper: NavigationHelper, character_cache_manager: ICharacterCacheDiscordManager, logger: logging.Logger): # Добавляем character_cache_manager
        self.navigation_helper = navigation_helper
        self.character_cache_manager = character_cache_manager # Инициализируем
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self, command_str: str, interaction: discord.Interaction) -> NavigationDisplayDataDTO:
        user = interaction.user
        guild = interaction.guild # Добавляем guild для доступа к сессии
        self.logger.debug(f"Выполняется ShowNavigationHandler для пользователя {user.name} с командой: {command_str}")

        try:
            # 1. Получаем детали текущей локации с помощью хелпера
            location_details: Dict[str, Any] = await self.navigation_helper.get_current_location_details_for_user(user)
            current_location_id = location_details.get("access_key", "") # Используем access_key как location_id

            # 🔥 НОВОЕ: Получаем ID предыдущей локации из сессии персонажа 🔥
            character_id = await self.character_cache_manager.get_active_character_id(user.id)
            if not character_id:
                raise ValueError(f"Не найден активный персонаж для пользователя {user.name}.")
            
            char_session = await self.character_cache_manager.get_character_session(character_id, guild.id)
            previous_location_data = char_session.get("location", {}).get("previous", {})
            previous_location_id = previous_location_data.get("location_id") if previous_location_data else None

            # 2. Подготавливаем данные для полей эмбеда (Fields) - без изменений, т.к. они берутся из exits
            location_fields: List[Dict[str, Any]] = []
            exits_data = location_details.get("exits", []) 

            if exits_data:
                location_fields.append({
                    "name": "🗺️ Доступные пути:",
                    "value": "Вы можете пойти:",
                    "inline": False
                })
                for i, exit_info in enumerate(exits_data):
                    label = exit_info.get("label", f"Путь {i+1}")
                    target_id = exit_info.get("target_location_id", "???")
                    location_fields.append({
                        "name": f"➡ {label}",
                        "value": f"(ID: {target_id})",
                        "inline": True
                    })
            else:
                location_fields.append({
                    "name": "🚫 Путей нет",
                    "value": "Из этой локации нет явных выходов.",
                    "inline": False
                })

            # 3. 🔥 НОВОЕ: Определяем описание локации на основе контекста 🔥
            location_name = location_details.get("name", "Неизвестная локация")
            location_description_key = location_details.get("description") # Получаем ключ из YAML

            final_location_description = "Описание отсутствует." # Дефолтное описание на случай ошибок

            if location_description_key and location_description_key in LOCATION_DESCRIPTIONS:
                context_descriptions = LOCATION_DESCRIPTIONS[location_description_key]
                if previous_location_id and previous_location_id in context_descriptions:
                    final_location_description = context_descriptions[previous_location_id]
                    self.logger.debug(f"Описание для {current_location_id} получено из контекста: предыдущая {previous_location_id}.")
                else:
                    final_location_description = context_descriptions.get("default", "Описание отсутствует.")
                    if previous_location_id: # Если предыдущая локация есть, но для неё нет специфичного описания
                         self.logger.warning(f"Для локации {current_location_id} (ключ: {location_description_key}) нет специфичного описания для входа из {previous_location_id}. Использовано дефолтное.")
                    else: # Если это первый вход или нет предыдущей локации
                         self.logger.debug(f"Для локации {current_location_id} (ключ: {location_description_key}) использовано дефолтное описание (нет предыдущей локации).")
            else:
                self.logger.warning(f"Для локации {current_location_id} не найден ключ описания ({location_description_key}) или он отсутствует в LOCATION_DESCRIPTIONS.")
                # Если ключа нет или он не найден, можно использовать старое доброе "Описание отсутствует." или что-то из самого YAML, если там вдруг останется.
                # Пока оставляем так, чтобы не было пустых описаний.

            # 4. Подготавливаем заглушку для амбиентного футера (без изменений)
            ambient_footer_placeholder_data = {
                "players_in_location": 0,
            }

            # 5. Формируем DTO для презентационного слоя
            unified_display_type = location_details.get("specific_category", "POI") # Используем specific_category для unified_display_type, т.к. presentation.unified_display_type удален. Если нужно другое поле, уточните.
            # Если вам нужно поле unified_display_type из оригинального description, его нужно будет вынести в YAML как отдельное поле
            # или определить его на основе specific_category, как я сделал здесь.
            
            # image_url теперь всегда будет None, так как поле presentation удалено
            image_url = None 

            navigation_data_dto = NavigationDisplayDataDTO(
                location_name=location_name,
                location_description=final_location_description, # Используем наше новое описание
                unified_display_type=unified_display_type,
                current_location_id=current_location_id,
                exits=exits_data,
                image_url=image_url, # image_url теперь всегда None
                location_fields_data=location_fields,
                ambient_footer_data=ambient_footer_placeholder_data
            )
            self.logger.debug(f"ShowNavigationHandler успешно сформировал DTO для {user.name}.")
            return navigation_data_dto

        except ValueError as e:
            self.logger.error(f"Ошибка получения данных локации для пользователя {user.name}: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в ShowNavigationHandler для {user.name}: {e}", exc_info=True)
            raise