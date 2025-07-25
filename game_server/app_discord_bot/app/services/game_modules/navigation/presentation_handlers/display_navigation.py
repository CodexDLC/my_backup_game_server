# game_server/app_discord_bot/app/services/navigation/presentation_handlers/display_navigation.py

import inject
import discord
import logging
import json

# Менеджеры кэша
from game_server.app_discord_bot.app.services.game_modules.navigation.dtos import NavigationDisplayDataDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

# DTOs


# Утилиты
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager

# Представления (Views)
from game_server.app_discord_bot.app.ui.views.navigation.navigation_views import (
    HubLocationView, 
    ExternalLocationView, 
    InternalLocationView,
    BaseNavigationView
)

class DisplayNavigationPresenter:
    """
    Презентационный обработчик для отображения навигационного интерфейса.
    Выбирает подходящий View и обновляет нижнее сообщение в Discord.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        interaction_response_manager: InteractionResponseManager,
        account_data_manager: IAccountDataManager,
        logger: logging.Logger,
    ):
        self.bot = bot
        self.interaction_response_manager = interaction_response_manager
        self.account_data_manager = account_data_manager
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(
        self, 
        data_dto: NavigationDisplayDataDTO, 
        interaction: discord.Interaction, 
        helpers=None,
        response_message_object: discord.Message | None = None
    ):
        user = interaction.user
        guild = interaction.guild
        self.logger.debug(f"Выполняется DisplayNavigationPresenter для пользователя {user.name}.")

        try:
            # 1. Выбираем подходящий View класс на основе unified_display_type
            view_data = {
                "location_info": {
                    "name": data_dto.location_name,
                    "description": data_dto.location_description,
                    "unified_display_type": data_dto.unified_display_type,
                    "location_id": data_dto.current_location_id,
                    "presentation": {"image_url": data_dto.image_url}
                },
                "transitions": data_dto.exits # Ваши "exits" это "transitions" для View (для кнопок)
            }

            ViewClass: type[BaseNavigationView]
            if data_dto.unified_display_type == "HUB_LOCATION":
                ViewClass = HubLocationView
            elif data_dto.unified_display_type == "INTERNAL_LOCATION":
                ViewClass = InternalLocationView
            else:
                ViewClass = ExternalLocationView

            navigation_view = ViewClass(author=user, data=view_data)
            footer_embed = navigation_view.create_embed() # Получаем базовый эмбед от View

            # 2. Добавляем изображение, если оно есть
            if data_dto.image_url:
                footer_embed.set_image(url=data_dto.image_url)

            # 3. Добавляем поля (Fields) из DTO
            for field_data in data_dto.location_fields_data:
                footer_embed.add_field(
                    name=field_data.get("name", "N/A"),
                    value=field_data.get("value", "N/A"),
                    inline=field_data.get("inline", False)
                )

            # 4. Добавляем футер, используя метод DTO
            footer_text = data_dto.format_ambient_footer_text()
            footer_embed.set_footer(text=footer_text)
            
            # 5. Получаем ID канала и ID сообщения для нижнего окна
            channels_data_json = await self.account_data_manager.get_hash_field(
                RedisKeys.PLAYER_ACCOUNT_DATA_HASH.format(shard_id=guild.id, discord_user_id=user.id),
                RedisKeys.FIELD_DISCORD_CHANNELS
            )
            channels_data = json.loads(channels_data_json)
            interface_channel_id = int(channels_data["interface_channel_id"])

            message_ids_data_json = await self.account_data_manager.get_hash_field(
                RedisKeys.PLAYER_ACCOUNT_DATA_HASH.format(shard_id=guild.id, discord_user_id=user.id),
                RedisKeys.FIELD_MESSAGES
            )
            message_ids_data = json.loads(message_ids_data_json)
            footer_msg_id = int(message_ids_data["footer_id"])

            interface_channel = guild.get_channel(interface_channel_id)
            if not interface_channel:
                raise ValueError(f"Не удалось найти канал интерфейса с ID: {interface_channel_id}")
            
            footer_msg = await interface_channel.fetch_message(footer_msg_id)
            
            # 6. Обновляем нижнее сообщение в Discord
            await footer_msg.edit(content="", embed=footer_embed, view=navigation_view)
            
            self.logger.info(f"Навигационный интерфейс для {user.name} успешно отрисован/обновлен.")

            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object)

        except ValueError as e:
            self.logger.error(f"Ошибка получения данных для отрисовки навигации для {user.name}: {e}")
            if response_message_object:
                await self.interaction_response_manager.edit_thinking_message(response_message_object, f"Не удалось отобразить навигацию: {e}")
            else:
                await self.interaction_response_manager.send_personal_notification_message(interaction, f"Не удалось отобразить навигацию: {e}")
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в DisplayNavigationPresenter для {user.name}: {e}", exc_info=True)
            if response_message_object:
                await self.interaction_response_manager.edit_thinking_message(response_message_object, "Произошла критическая ошибка при отображении навигации.")
            else:
                await self.interaction_response_manager.send_personal_notification_message(interaction, "Произошла критическая ошибка при отображении навигации.")