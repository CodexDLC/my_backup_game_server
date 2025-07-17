# --- Файл: game_server/app_discord_bot/app/ui/components/buttons/main_panel_buttons.py ---

import discord

class ProfileButton(discord.ui.Button):
    """Кнопка для вызова меню 'Профиль' (синяя)."""
    def __init__(self, **kwargs):
        super().__init__(label="Профиль", emoji="👤", style=discord.ButtonStyle.primary, **kwargs)

class InventoryButton(discord.ui.Button):
    """Кнопка для вызова 'Инвентаря' (синяя)."""
    def __init__(self, **kwargs):
        super().__init__(label="Инвентарь", emoji="🎒", style=discord.ButtonStyle.primary, **kwargs)

class SkillsButton(discord.ui.Button):
    """Кнопка для вызова меню 'Навыки' (синяя)."""
    def __init__(self, **kwargs):
        super().__init__(label="Навыки", emoji="✨", style=discord.ButtonStyle.primary, **kwargs)

# 🔥 НОВОЕ: Кнопка "Навигация" вместо "Карты"
class NavigationButton(discord.ui.Button):
    """Кнопка для вызова 'Навигации' (синяя)."""
    def __init__(self, **kwargs):
        super().__init__(label="Навигация", emoji="🗺️", style=discord.ButtonStyle.primary, **kwargs)

class LogoutButton(discord.ui.Button):
    """Кнопка для выхода из игровой сессии (красная)."""
    def __init__(self, **kwargs):
        super().__init__(label="Выход", emoji="🚪", style=discord.ButtonStyle.danger, **kwargs)

class SettingsButton(discord.ui.Button):
    """Кнопка для доступа к настройкам (серая)."""
    def __init__(self, **kwargs):
        super().__init__(label="Настройки", emoji="⚙️", style=discord.ButtonStyle.secondary, **kwargs)