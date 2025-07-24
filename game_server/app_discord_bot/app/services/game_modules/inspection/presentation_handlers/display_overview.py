# game_server/app_discord_bot/app/services/game_modules/inspection/presentation_handlers/display_overview.py

import discord
import inject
import logging

# ИСПОЛЬЗУЕМ АБСОЛЮТНЫЕ ИМПОРТЫ
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import LookAroundResultDTO
from game_server.app_discord_bot.app.ui.views.inspection.overview_views import OverviewCategoriesView
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_templates import get_category_description
# from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager # УДАЛЯЕМ ИМПОРТ


class DisplayOverviewPresenter:
    """
    Презентер для отображения экрана общего обзора локации (Уровень 1).
    Редактирует постоянное "футер" сообщение игрока, отображая два эмбеда
    (динамические сущности и окружение) и кнопки категорий.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, account_data_manager: AccountDataManager): # УДАЛЯЕМ interaction_response_manager из __init__
        self.logger = logger
        self.account_data_manager = account_data_manager
        # self.interaction_response_manager = interaction_response_manager # УДАЛЯЕМ ИНИЦИАЛИЗАЦИЮ

    async def execute(self, dto: LookAroundResultDTO, interaction: discord.Interaction, **kwargs):
        self.logger.info(f"Отрисовка обзора локации для пользователя {interaction.user.id}")

        # Шаг 0: Отправляем кастомное "думает..." сообщение - ЭТО УДАЛЕНО, Т.К. ДЕЛАЕТСЯ В ROUTER
        # thinking_message = await self.interaction_response_manager.send_thinking_message(interaction)

        try:
            # Шаг 1: Получаем ID футер-сообщения из Redis
            messages_data = await self.account_data_manager.get_account_field(
                shard_id=interaction.guild.id,
                discord_user_id=interaction.user.id,
                field_name="messages"
            )
            if not messages_data or "footer_id" not in messages_data:
                self.logger.error(f"Не найден footer_id для пользователя {interaction.user.id}")
                # await self.interaction_response_manager.complete_thinking_message(thinking_message) # УДАЛЕНО
                await interaction.followup.send("Ошибка: не удалось найти ваше основное сообщение для обновления. Возможно, оно было удалено.", ephemeral=True)
                return

            footer_message_id = int(messages_data["footer_id"])

            # Шаг 2: Создаем новый контент (Два Embed и View)
            embeds = []

            # Верхний эмбед ("Активность в локации")
            if dto.dynamic_entities:
                dynamic_embed = discord.Embed(
                    title="Активность в локации",
                    description="Вы ощущаете присутствие...",
                    color=discord.Color.blurple()
                )
                for obj in dto.dynamic_entities:
                    field_value = get_category_description(obj.category_key, obj.count)
                    if field_value:
                        dynamic_embed.add_field(name=obj.display_name, value=field_value, inline=False)
                embeds.append(dynamic_embed)

            # Нижний эмбед ("Окружение")
            if dto.environmental_objects:
                environmental_embed = discord.Embed(
                    title="Окружение",
                    description="Вокруг вас объекты, с которыми можно взаимодействовать.",
                    color=discord.Color.dark_grey()
                )
                for obj in dto.environmental_objects:
                    field_value = get_category_description(obj.category_key, obj.count)
                    if field_value:
                        environmental_embed.add_field(name=obj.display_name, value=field_value, inline=False)
                embeds.append(environmental_embed)
            
            # Если нет ни динамических сущностей, ни объектов окружения
            if not embeds:
                self.logger.info(f"В локации нет отображаемых динамических сущностей или объектов окружения для пользователя {interaction.user.id}")
                no_data_embed = discord.Embed(
                    title="Осмотреться",
                    description="Кажется, здесь ничего интересного. Пусто.",
                    color=discord.Color.dark_orange()
                )
                embeds.append(no_data_embed)

            all_categories_for_buttons = dto.dynamic_entities + dto.environmental_objects
            view = OverviewCategoriesView(author=interaction.user, categories_data=all_categories_for_buttons)


            # Шаг 3: Находим и редактируем футер-сообщение
            footer_message = await interaction.channel.fetch_message(footer_message_id)
            await footer_message.edit(embeds=embeds, view=view)
            
            # Шаг 4: Завершаем кастомное "думает..." сообщение - ЭТО УДАЛЕНО, Т.К. ДЕЛАЕТСЯ В ORCHESTRATOR
            # await self.interaction_response_manager.complete_thinking_message(thinking_message)

        except discord.NotFound:
            self.logger.error(f"Не удалось найти футер-сообщение с ID {footer_message_id} для пользователя {interaction.user.id}")
            # await self.interaction_response_manager.complete_thinking_message(thinking_message) # УДАЛЕНО
            await interaction.followup.send("Ошибка: ваше основное сообщение было удалено или не найдено.", ephemeral=True)
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при отрисовке обзора локации: {e}", exc_info=True)
            # await self.interaction_response_manager.complete_thinking_message(thinking_message) # УДАЛЕНО
            await interaction.followup.send("Произошла непредвиденная ошибка.", ephemeral=True)