# /app/game_server/app_discord_bot/app/cogs/system/interaction_router.py

import inject
import discord
import logging
from discord.ext import commands

from game_server.app_discord_bot.config.router_config import SERVICE_MAP
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager


class InteractionRouter(commands.Cog):
    """
    Глобальный слушатель, который ловит все нажатия на компоненты
    и маршрутизирует их в нужный сервис.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger, 
                 interaction_response_manager: InteractionResponseManager):
        self.bot = bot
        self.logger = logger
        self.interaction_response_manager = interaction_response_manager
        self.logger.info("[+] Глобальный слушатель интеракций активен.")

    @commands.Cog.listener('on_interaction')
    async def main_interaction_router(self, interaction: discord.Interaction):
        # Проверяем, что это не команда слеш-команда и что есть custom_id
        if not interaction.data or 'custom_id' not in interaction.data:
            return

        custom_id = interaction.data['custom_id']
        self.logger.info(f"[ROUTER] Поймана интеракция с custom_id: '{custom_id}'")

        # НОВОЕ: Проверяем формат custom_id перед попыткой маршрутизации
        # Ожидаем, что custom_id для маршрутизации будет содержать хотя бы одно двоеточие (:)
        # Если двоеточия нет, это, вероятно, auto-generated ID компонента, который обрабатывается внутри View.
        if ':' not in custom_id:
            self.logger.critical(f"[ROUTER] CRITICAL: custom_id '{custom_id}' не содержит двоеточия. Игнорирую, так как это, вероятно, внутренний ID компонента View.") # НОВЫЙ CRITICAL ЛОГ
            return

        # Если custom_id содержит двоеточие, продолжаем маршрутизацию
        service_name, command_for_orchestrator = custom_id.split(':', 1)

        OrchestratorClass = SERVICE_MAP.get(service_name)

        if not OrchestratorClass:
            self.logger.warning(f"[ROUTER] Оркестратор для сервиса '{service_name}' не найден. Игнорирую.")
            return

        try:
            # ✅ НОВАЯ ПРОВЕРКА:
            # Проверяем, есть ли у interaction наш флаг.
            # hasattr нужен, чтобы не было ошибки на настоящих интеракциях.
            is_background_event = getattr(interaction, 'is_background_event', False)

            response_message_object = None
            if not is_background_event:
                # Если это НЕ фоновое событие, то отправляем "Думаю..."
                response_message_object = await self.interaction_response_manager.send_thinking_message(interaction)

            orchestrator_instance = inject.instance(OrchestratorClass)

            self.logger.info(f"[ROUTER] Передаю управление в оркестратор '{service_name}'...")
            await orchestrator_instance.process(command_for_orchestrator, interaction, response_message_object)
            self.logger.info(f"[ROUTER] Оркестратор '{service_name}' успешно завершил работу.")

        except Exception as e:
            self.logger.error(f"[ROUTER] КРИТИЧЕСКАЯ ОШИБКА в оркестраторе '{service_name}': {e}", exc_info=True)
            
            # ✅ НОВАЯ ПРОВЕРКА:
            # Сначала проверяем, является ли это фоновым событием.
            # Если да, то мы просто логируем ошибку и ничего не отправляем в Discord.
            is_background_event = getattr(interaction, 'is_background_event', False)
            if is_background_event:
                self.logger.debug("[ROUTER] Ошибка произошла в фоновом событии, ответ пользователю не отправляется.")
                return

            # Если это НЕ фоновое событие, используем старую логику для ответа пользователю.
            if not interaction.response.is_done():
                await interaction.response.send_message("Произошла критическая ошибка при обработке вашего действия.", ephemeral=True)
            elif response_message_object: # is_done() здесь уже подразумевается
                await response_message_object.edit(content="Произошла критическая ошибка при обработке вашего действия. Пожалуйста, сообщите администратору.", view=None, delete_after=None)
            else:
                self.logger.warning("Не удалось отправить сообщение об ошибке пользователю, interaction.response уже done, но нет response_message_object.")

