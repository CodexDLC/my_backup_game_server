import discord

class RegistrationView(discord.ui.View):
    """
    Постоянный View для сообщения регистрации.
    Кнопки содержат в custom_id полные команды для роутера.
    """
    def __init__(self, **kwargs):
        # Оставляем **kwargs для совместимости с message_sender_service
        super().__init__(timeout=None)

        # Кнопка "Зарегистрироваться"
        # Полный формат: 'сервис:команда'
        self.add_item(discord.ui.Button(
            label="Зарегистрироваться",
            style=discord.ButtonStyle.success,
            # ▼▼▼ УБЕДИТЕСЬ, ЧТО ЗДЕСЬ ПОЛНАЯ КОМАНДА ▼▼▼
            custom_id="authentication:start_registration"
        ))

        # Кнопка "FAQ"
        self.add_item(discord.ui.Button(
            label="FAQ / Помощь",
            style=discord.ButtonStyle.secondary,
            # ▼▼▼ УБЕДИТЕСЬ, ЧТО ЗДЕСЬ ПОЛНАЯ КОМАНДА ▼▼▼
            custom_id="authentication:show_faq"
        ))