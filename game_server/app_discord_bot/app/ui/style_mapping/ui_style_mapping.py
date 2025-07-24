# game_server/app_discord_bot/app/ui/style_mapping/ui_style_mapping.py

import discord

# Карта для преобразования абстрактных строковых стилей в конкретные объекты discord.ButtonStyle
DISCORD_BUTTON_STYLES = {
    "primary": discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
    "link": discord.ButtonStyle.link,
    "blurple": discord.ButtonStyle.blurple, # Для Discord.py 2.0+
    "green": discord.ButtonStyle.green,       # Добавлен green
    "grey": discord.ButtonStyle.grey,       # Для Discord.py 2.0+
}

def get_discord_button_style(abstract_style: str) -> discord.ButtonStyle:
    """
    Возвращает объект discord.ButtonStyle на основе абстрактного строкового имени стиля.
    Используется для отвязки логики от конкретных стилей Discord.py.
    """
    return DISCORD_BUTTON_STYLES.get(abstract_style, discord.ButtonStyle.secondary)

