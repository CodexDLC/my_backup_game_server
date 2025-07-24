# game_server\app_discord_bot\app\services\authentication\lobby\presentation_handlers\display_game_interface_handler.py

import inject
import discord
import logging
import json

# Менеджеры кэша
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheDiscordManager

# Ключи и DTO
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.core.contracts.handler_response_dto import LoginSuccessDTO

# Утилиты и UI
from game_server.app_discord_bot.app.services.utils.navigation_helper import NavigationHelper
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager
from game_server.app_discord_bot.app.ui.views.system.main_panel_view import MainPanelView
from game_server.app_discord_bot.app.ui.views.navigation.navigation_views import HubLocationView, ExternalLocationView, InternalLocationView


class DisplayGameInterfacePresenter:
    """
    "Умный" презентер, отвечающий за отрисовку основного игрового интерфейса
    (верхней панели и нижнего контент-окна) при входе в игру.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: discord.Client,
        character_cache_manager: ICharacterCacheDiscordManager,
        interaction_response_manager: InteractionResponseManager,
        logger: logging.Logger,
        navigation_helper: NavigationHelper,
        account_data_manager: IAccountDataManager
    ):
        self.bot = bot
        self.character_cache_manager = character_cache_manager
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger
        self.navigation_helper = navigation_helper
        self.account_data_manager = account_data_manager

    async def execute(self, response_dto: LoginSuccessDTO, interaction: discord.Interaction, helpers, response_message_object: discord.Message | None = None):
        user = interaction.user
        guild = interaction.guild

        try:
            # --- 1. Получение данных из кэша ---
            self.logger.info(f"Начало отрисовки игрового интерфейса для {user.name}.")
            
            character_id = await self.character_cache_manager.get_active_character_id(user.id)
            if not character_id:
                raise ValueError("Не найдена активная сессия персонажа для отрисовки.")

            character_session = await self.character_cache_manager.get_character_session(character_id, guild.id)
            if not character_session:
                raise ValueError(f"Не найден кэш для сессии персонажа {character_id}.")

            location_details = await self.navigation_helper.get_current_location_details_for_user(user)
            
            # --- 2. Сборка UI ---
            main_panel_view = MainPanelView(author=user, character_core_data=character_session)
            header_embed = main_panel_view.create_header_embed()

            location_display_type = location_details.get("unified_display_type")
            
            nav_data_for_view = {
                "location_info": location_details,
                "transitions": location_details.get("exits", [])
            }
            
            view_map = {
                "HUB_LOCATION": HubLocationView,
                "INTERNAL_LOCATION": InternalLocationView,
            }
            ViewClass = view_map.get(location_display_type, ExternalLocationView)
            navigation_view = ViewClass(author=user, data=nav_data_for_view)
            footer_embed = navigation_view.create_embed()

            # --- 3. Обновление сообщений в Discord ---

            # Шаг 3.1: Получаем ID канала
            channels_data_json = await self.account_data_manager.get_hash_field(
                RedisKeys.PLAYER_ACCOUNT_DATA_HASH.format(shard_id=guild.id, discord_user_id=user.id),
                RedisKeys.FIELD_DISCORD_CHANNELS
            )
            channels_data = json.loads(channels_data_json)
            interface_channel_id = int(channels_data["interface_channel_id"])

            # Шаг 3.2: Получаем ID сообщений
            message_ids_data_json = await self.account_data_manager.get_hash_field(
                RedisKeys.PLAYER_ACCOUNT_DATA_HASH.format(shard_id=guild.id, discord_user_id=user.id),
                RedisKeys.FIELD_MESSAGES
            )
            message_ids_data = json.loads(message_ids_data_json)
            header_msg_id = int(message_ids_data["top_id"])
            footer_msg_id = int(message_ids_data["footer_id"])

            interface_channel = guild.get_channel(interface_channel_id)
            if not interface_channel:
                raise ValueError(f"Не удалось найти канал интерфейса с ID: {interface_channel_id}")
            
            header_msg = await interface_channel.fetch_message(header_msg_id)
            footer_msg = await interface_channel.fetch_message(footer_msg_id)
            
            await header_msg.edit(content="", embed=header_embed, view=main_panel_view)
            await footer_msg.edit(content="", embed=footer_embed, view=navigation_view)
            
            self.logger.info(f"Игровой интерфейс для {user.name} успешно отрисован/обновлен.")

            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object)

        except Exception as e:
            self.logger.error(f"Критическая ошибка в DisplayGameInterfacePresenter для {user.name}: {e}", exc_info=True)
            if interaction:
                 await self.interaction_response_manager.send_personal_notification_message(interaction, "Произошла критическая ошибка при отрисовке интерфейса.")