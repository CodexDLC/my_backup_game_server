# game_server/app_discord_bot/app/ui/components/views/registration_view.py
import discord
import inject
import logging

# 🔥 ИЗМЕНЕНИЕ 1: Удаляем импорты низкоуровневых зависимостей и flow
# from game_server.app_discord_bot.app.services.authentication.flows.hub_registration_flow import execute_hub_registration_flow
# from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
# from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
# from game_server.app_discord_bot.storage.cache.managers.guild_config_manager 

# 🔥 ИЗМЕНЕНИЕ 2: Импортируем только AuthenticationService
from game_server.app_discord_bot.app.services.authentication.authentication_service import AuthenticationService
# ▼▼▼ ИМПОРТИРУЕМ КЛАССЫ КНОПОК ИЗ РЕФАКТОРИНГОВОЙ СТРУКТУРЫ ▼▼▼

from game_server.app_discord_bot.app.ui.components.buttons.authentication_buttons import RegisterButton
from game_server.app_discord_bot.app.ui.messages.authentication.registration_messages import FAQ_MESSAGE_CONTENT


class RegistrationView(discord.ui.View):
    """
    Постоянный View для сообщения регистрации, содержащий кнопки "Зарегистрироваться" и "FAQ/Помощь".
    """
    def __init__(self, bot_instance: discord.Client):
        super().__init__(timeout=None)
        self.bot_instance = bot_instance
        self.logger = inject.instance(logging.Logger)
        
        # ▼▼▼ Создаем экземпляр RegisterButton, привязываем коллбэк и добавляем его ▼▼▼
        register_button = RegisterButton(custom_id="persistent_register_button", row=0)
        register_button.callback = self.on_register # Привязываем коллбэк
        self.add_item(register_button)

        # ▼▼▼ Создаем кнопку "FAQ / Помощь" вручную, привязываем коллбэк и добавляем ее ▼▼▼
        faq_button = discord.ui.Button(
            label="FAQ / Помощь",
            style=discord.ButtonStyle.secondary,
            custom_id="persistent_faq_button",
            row=0
        )
        faq_button.callback = self.faq_button_callback # Привязываем коллбэк
        self.add_item(faq_button)

    # ▼▼▼ МЕТОД-КОЛЛБЭК ТЕПЕРЬ БЕЗ ДЕКОРАТОРА @discord.ui.button (привязка происходит в __init__) ▼▼▼
    async def on_register(self, interaction: discord.Interaction):
        """
        Метод-обработчик, вызываемый кнопкой RegisterButton.
        Делегирует весь процесс сервису аутентификации.
        """
        self.logger.info(f"Кнопка 'Зарегистрироваться' нажата пользователем: {interaction.user.name} ({interaction.user.id})")
        
        try:
            # 🔥 ИЗМЕНЕНИЕ 3: Получаем один сервис и вызываем один его метод.
            # View больше не знает о деталях реализации регистрации.
            authentication_service = inject.instance(AuthenticationService)
            await authentication_service.start_hub_registration(interaction)
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка в RegistrationView.on_register для {interaction.user.id}: {e}", exc_info=True)
            # Ответ пользователю теперь будет отправляться изнутри start_hub_registration,
            # но на случай падения до ответа, оставим этот блок.
            if not interaction.response.is_done():
                await interaction.followup.send("Произошла ошибка при регистрации. Пожалуйста, попробуйте позже или свяжитесь с администрацией.", ephemeral=True)

    # ▼▼▼ МЕТОД-КОЛЛБЭК ТЕПЕРЬ БЕЗ ДЕКОРАТОРА @discord.ui.button (привязка происходит в __init__) ▼▼▼
    async def faq_button_callback(self, interaction: discord.Interaction):
        """
        Обработчик нажатия кнопки "FAQ / Помощь".
        """
        self.logger.info(f"Кнопка 'FAQ / Помощь' нажата пользователем: {interaction.user.name} ({interaction.user.id})")
        await interaction.response.send_message(FAQ_MESSAGE_CONTENT, ephemeral=True)
