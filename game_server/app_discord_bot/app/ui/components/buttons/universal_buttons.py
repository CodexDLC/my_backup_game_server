# --- Файл: game_server/app_discord_bot/app/ui/components/buttons/universal_buttons.py ---

import discord

class BackButton(discord.ui.Button):
    """Универсальная кнопка 'Назад' (серая)."""
    def __init__(self, label: str = "Назад", **kwargs):
        super().__init__(label=label, emoji="⬅️", style=discord.ButtonStyle.secondary, **kwargs)

class ConfirmButton(discord.ui.Button):
    """Универсальная кнопка 'Подтвердить' (зеленая)."""
    def __init__(self, label: str = "Подтвердить", **kwargs):
        super().__init__(label=label, emoji="✔️", style=discord.ButtonStyle.success, **kwargs)

class CancelButton(discord.ui.Button):
    """Универсальная кнопка 'Отмена' или 'Закрыть' (серая)."""
    def __init__(self, label: str = "Отмена", **kwargs):
        super().__init__(label=label, emoji="❌", style=discord.ButtonStyle.secondary, **kwargs)

class DeleteButton(discord.ui.Button):
    """Универсальная кнопка для опасного действия 'Удалить' (красная)."""
    def __init__(self, label: str = "Удалить", **kwargs):
        super().__init__(label=label, emoji="🔥", style=discord.ButtonStyle.danger, **kwargs)

class ObserveButton(discord.ui.Button):
    """Кнопка для действия 'Осмотреться' в локации (серая)."""
    def __init__(self, label: str = "Осмотреться", **kwargs):
        super().__init__(label=label, emoji="👀", style=discord.ButtonStyle.secondary, **kwargs)

class ExitButton(discord.ui.Button):
    """Универсальная кнопка 'Выйти' (серая)."""
    def __init__(self, label: str = "Выйти", **kwargs):
        super().__init__(label=label, emoji="🚪", style=discord.ButtonStyle.secondary, **kwargs)