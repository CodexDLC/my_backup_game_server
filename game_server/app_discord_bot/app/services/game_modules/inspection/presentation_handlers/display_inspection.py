# game_server/app_discord_bot/app/services/game_modules/inspection/presentation_handlers/display_inspection_list.py

import discord
import inject
import logging
from typing import Type

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import InspectionListDTO
from game_server.app_discord_bot.app.ui.embed_factories.list_embed_factory import LIST_EMBED_FACTORIES, create_default_list_embeds
from game_server.app_discord_bot.app.ui.views.inspection.inspection_list_views import BaseCategoryListView
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager



class DisplayInspectionListPresenter:
    """
    Презентер для отображения списка объектов в выбранной категории (Уровень 2).
    Действует как диспетчер, вызывая соответствующую фабрику для создания эмбедов.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, account_data_manager: AccountDataManager):
        self.logger = logger
        self.account_data_manager = account_data_manager
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self, dto: InspectionListDTO, interaction: discord.Interaction, **kwargs):
        self.logger.info(f"Отрисовка списка категории '{dto.title}' для пользователя {interaction.user.id}")

        try:
            # Шаг 1: Получаем ID футер-сообщения из Redis
            messages_data = await self.account_data_manager.get_account_field(
                shard_id=interaction.guild.id,
                discord_user_id=interaction.user.id,
                field_name="messages"
            )
            if not messages_data or "footer_id" not in messages_data:
                self.logger.error(f"Не найден footer_id для пользователя {interaction.user.id}")
                await interaction.followup.send("Ошибка: не удалось найти ваше основное сообщение для обновления.", ephemeral=True)
                return

            footer_message_id = int(messages_data["footer_id"])

            # --- Шаг 2: Создание контента с помощью Фабрики ---
            
            # 2.1. Находим нужную фабрику в реестре. Если для категории нет своей фабрики,
            # используем фабрику по умолчанию (которая создает 2 колонки).
            embed_factory_func = LIST_EMBED_FACTORIES.get(dto.pagination.category_key, create_default_list_embeds)
            
            # 2.2. Вызываем фабрику, чтобы получить готовый список эмбедов
            embeds = embed_factory_func(dto)
            
            # 2.3. Создаем View
            view = BaseCategoryListView(author=interaction.user, dto=dto)
            
            # Если фабрика не вернула ни одного эмбеда (например, все списки пусты)
            if not embeds:
                no_data_embed = discord.Embed(
                    title=f"{dto.title} (Страница {dto.pagination.current_page}/{dto.pagination.total_pages})",
                    description="В этой категории пока ничего нет.",
                    color=discord.Color.orange()
                )
                embeds.append(no_data_embed)


            # --- Шаг 3: Находим и редактируем футер-сообщение ---
            footer_message = await interaction.channel.fetch_message(footer_message_id)
            await footer_message.edit(embeds=embeds, view=view)

        except discord.NotFound:
            self.logger.error(f"Не удалось найти футер-сообщение с ID {footer_message_id} для пользователя {interaction.user.id}")
            await interaction.followup.send("Ошибка: ваше основное сообщение было удалено или не найдено.", ephemeral=True)
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при отрисовке списка категории: {e}", exc_info=True)
            await interaction.followup.send("Произошла непредвиденная ошибка при отображении списка.", ephemeral=True)