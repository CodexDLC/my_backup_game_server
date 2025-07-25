# game_server/app_discord_bot/app/services/game_modules/inspection/presentation_handlers/display_entity_details.py

import discord
import inject
import logging
from typing import Type, Dict

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import EntityDetailsDTO
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
# Обновляем импорт View-классов
from game_server.app_discord_bot.app.ui.views.inspection.entity_details_views import (
    BaseEntityDetailsView, 
    PlayerDetailsView, 
    NpcDetailsView, 
    MonsterDetailsView
)


class DisplayEntityDetailsPresenter:
    """
    Презентер для отображения экрана детального осмотра сущности (Уровень 3).
    Динамически выбирает подходящий View для категории сущности.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, account_data_manager: AccountDataManager):
        self.logger = logger
        self.account_data_manager = account_data_manager
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

        # Карта для динамического выбора View (ОБНОВЛЕНА)
        self.entity_details_view_map: Dict[str, Type[BaseEntityDetailsView]] = {
            "players": PlayerDetailsView,
            "npc_neutral": NpcDetailsView,
            "npc_enemy": MonsterDetailsView,
            # TODO: Добавляйте сюда другие специализированные View по мере их создания
            # "chests": ChestDetailsView,
        }

    async def execute(self, dto: EntityDetailsDTO, interaction: discord.Interaction, **kwargs):
        self.logger.info(f"Отрисовка деталей сущности '{dto.title}' для пользователя {interaction.user.id}")

        try:
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

            embed = discord.Embed(
                title=dto.title,
                description=dto.description,
                color=discord.Color.dark_blue()
            )

            if dto.image_url:
                embed.set_image(url=dto.image_url)

            for field_data in dto.fields:
                embed.add_field(
                    name=field_data.get("name", "N/A"),
                    value=field_data.get("value", "N/A"),
                    inline=field_data.get("inline", False)
                )

            ViewClass = self.entity_details_view_map.get(dto.category_key, BaseEntityDetailsView)
            view = ViewClass(author=interaction.user, dto=dto)

            footer_message = await interaction.channel.fetch_message(footer_message_id)
            await footer_message.edit(embed=embed, view=view)

        except discord.NotFound:
            self.logger.error(f"Не удалось найти футер-сообщение с ID {footer_message_id} для пользователя {interaction.user.id}")
            await interaction.followup.send("Ошибка: ваше основное сообщение было удалено или не найдено.", ephemeral=True)
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при отрисовке деталей сущности: {e}", exc_info=True)
            await interaction.followup.send("Произошла непредвиденная ошибка.", ephemeral=True)