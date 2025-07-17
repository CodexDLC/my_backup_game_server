import discord

from game_server.app_discord_bot.app.ui.components.buttons.authentication_buttons import LoginButton

# ▼▼▼ ИМПОРТИРУЕМ КЛАССЫ КНОПОК ▼▼▼


class LoginView(discord.ui.View):
    """
    Постоянный View для сообщения логина, содержащий кнопку "Войти в игру".
    """
    def __init__(self, bot_instance: discord.Client):
        super().__init__(timeout=None)
        
        # 🔥 ИЗМЕНЕНИЕ: Убираем callback, добавляем custom_id
        # Теперь эта кнопка будет запускать наш новый архитектурный цикл
        login_button = LoginButton(
            row=0, 
            custom_id="authentication:start_login"
        )
        self.add_item(login_button)
        
        # Старый метод on_login() можно полностью удалить из этого класса.
