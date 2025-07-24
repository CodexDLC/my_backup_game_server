# game_server/app_discord_bot/app/services/navigation/logic_handlers/show_navigation.py

import inject
import discord
import logging
from typing import Dict, Any, List # Добавлен List


from game_server.app_discord_bot.app.services.game_modules.navigation.dtos import NavigationDisplayDataDTO
from game_server.app_discord_bot.app.services.utils.navigation_helper import NavigationHelper

class ShowNavigationHandler:
    """
    Логический обработчик для команды 'show_navigation'.
    Получает данные о текущей локации и подготавливает их для презентации.
    """
    @inject.autoparams()
    def __init__(self, navigation_helper: NavigationHelper, logger: logging.Logger):
        self.navigation_helper = navigation_helper
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self, command_str: str, interaction: discord.Interaction) -> NavigationDisplayDataDTO:
        user = interaction.user
        self.logger.debug(f"Выполняется ShowNavigationHandler для пользователя {user.name} с командой: {command_str}")

        try:
            # 1. Получаем детали текущей локации с помощью хелпера
            location_details: Dict[str, Any] = await self.navigation_helper.get_current_location_details_for_user(user)

            # 2. Подготавливаем данные для полей эмбеда (Fields)
            # Формируем список выходов для отображения в Fields
            location_fields: List[Dict[str, Any]] = []
            exits_data = location_details.get("exits", []) 

            if exits_data:
                # Заголовок для поля с выходами
                location_fields.append({
                    "name": "🗺️ Доступные пути:",
                    "value": "Вы можете пойти:",
                    "inline": False # Отдельная строка для заголовка путей
                })
                # Каждое направление как отдельное поле
                for i, exit_info in enumerate(exits_data):
                    label = exit_info.get("label", f"Путь {i+1}")
                    target_id = exit_info.get("target_location_id", "???")
                    location_fields.append({
                        "name": f"➡ {label}", # Имя поля
                        "value": f"(ID: {target_id})", # Значение поля, например, ID локации
                        "inline": True # Располагаем их инлайн
                    })
            else:
                location_fields.append({
                    "name": "🚫 Путей нет",
                    "value": "Из этой локации нет явных выходов.",
                    "inline": False
                })

            # 3. Подготавливаем заглушку для амбиентного футера
            ambient_footer_placeholder_data = {
                "players_in_location": 0, # Дефолтное значение
                # "npcs_in_location": 0, # Можно добавить другие заглушки
            }

            # 4. Формируем DTO для презентационного слоя
            location_name = location_details.get("name", "Неизвестная локация")
            location_description = location_details.get("description", "Описание отсутствует.")
            unified_display_type = location_details.get("unified_display_type", "EXTERNAL_LOCATION")
            current_location_id = location_details.get("location_id", "")
            image_url = location_details.get("presentation", {}).get("image_url")


            navigation_data_dto = NavigationDisplayDataDTO(
                location_name=location_name,
                location_description=location_description,
                unified_display_type=unified_display_type,
                current_location_id=current_location_id,
                exits=exits_data, # Оригинальные exits, они нужны View для кнопок
                image_url=image_url,
                location_fields_data=location_fields, # Данные для Fields
                ambient_footer_data=ambient_footer_placeholder_data # Данные для футера
            )
            self.logger.debug(f"ShowNavigationHandler успешно сформировал DTO для {user.name}.")
            return navigation_data_dto

        except ValueError as e:
            self.logger.error(f"Ошибка получения данных локации для пользователя {user.name}: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в ShowNavigationHandler для {user.name}: {e}", exc_info=True)
            raise