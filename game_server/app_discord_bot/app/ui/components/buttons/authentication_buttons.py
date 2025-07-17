# game_server/app_discord_bot/app/ui/components/buttons/authentication_buttons.py

import discord

class LoginButton(discord.ui.Button):
    """Кнопка для начала сессии 'Войти в игру' (синяя)."""
    def __init__(self, **kwargs):
        # Убираем callback и custom_id, они задаются в View при создании экземпляра
        super().__init__(label="Войти в игру", emoji="▶️", style=discord.ButtonStyle.primary, **kwargs)

class CharactersButton(discord.ui.Button):
    """Кнопка для перехода к выбору персонажа 'Персонажи' (синяя)."""
    def __init__(self, **kwargs):
        super().__init__(label="Персонажи", emoji="👥", style=discord.ButtonStyle.primary, **kwargs)

class DeckButton(discord.ui.Button):
    """Кнопка для меню 'Колода' (серая)."""
    def __init__(self, **kwargs):
        # Убираем disabled=True, чтобы на кнопку можно было нажать и получить заглушку
        super().__init__(label="Колода", emoji="🃏", style=discord.ButtonStyle.secondary, **kwargs)

class EnterWorldButton(discord.ui.Button):
    """Кнопка для подтверждения выбора персонажа 'Войти в мир' (зеленая)."""
    def __init__(self, **kwargs):
        super().__init__(label="Войти в мир", emoji="✅", style=discord.ButtonStyle.success, **kwargs)

class StartAdventureButton(discord.ui.Button):
    """Кнопка для запуска процесса начала приключения (зеленая)."""
    def __init__(self, **kwargs):
        super().__init__(label="Начать приключение", emoji="✨", style=discord.ButtonStyle.success, **kwargs)

# --- НОВАЯ КНОПКА ---
class LogoutButton(discord.ui.Button):
    """Кнопка для выхода из лобби (красная)."""
    def __init__(self, **kwargs):
        super().__init__(label="Разлогиниться", emoji="🚪", style=discord.ButtonStyle.danger, **kwargs)


class RegisterButton(discord.ui.Button):
    """
    Кнопка для начала процесса регистрации пользователя (зеленая).
    Делегирует действие методу on_register.
    """
    def __init__(self, custom_id: str = "register_button", row: int = 0):
        super().__init__(
            label="Зарегистрироваться",
            style=discord.ButtonStyle.success,
            emoji="✅",
            custom_id=custom_id,
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_register'):
            await self.view.on_register(interaction)
        else:
            await interaction.response.send_message("Функция регистрации временно недоступна.", ephemeral=True)