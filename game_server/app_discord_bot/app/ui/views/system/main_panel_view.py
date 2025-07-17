# game_server\app_discord_bot\app\ui\views\system\main_panel_view.py

import discord
from typing import Dict, Any

# Импортируем все необходимые кнопки
from game_server.app_discord_bot.app.ui.components.buttons.main_panel_buttons import (
    ProfileButton, 
    InventoryButton, 
    SkillsButton, 
    NavigationButton,
    LogoutButton,
    SettingsButton  # Добавили кнопку настроек
)

class MainPanelView(discord.ui.View):
    """
    Основная навигационная панель, которая отображается в верхнем сообщении.
    """
    def __init__(self, author: discord.User, character_core_data: Dict[str, Any]):
        super().__init__(timeout=None)
        self.author = author
        self.character_data = character_core_data

        # --- Макет 3x2 ---

        # Верхний ряд: Навигация и система
        self.add_item(NavigationButton(custom_id="navigation:show_navigation", row=0))
        self.add_item(SettingsButton(custom_id="settings:show_settings", row=0))
        self.add_item(LogoutButton(custom_id="system:logout", row=0))

        # Нижний ряд: Функции персонажа
        self.add_item(ProfileButton(custom_id="profile:show_profile", row=1))
        self.add_item(InventoryButton(custom_id="inventory:show_inventory", row=1))
        self.add_item(SkillsButton(custom_id="skills:show_skills", row=1))
        
    def create_header_embed(self) -> discord.Embed:
        """
        Создает эмбед для верхнего ("эмбиент") сообщения.
        """
        char_name = self.character_data.get("name", "Неизвестный герой")
        char_surname = self.character_data.get("surname", "")
        
        embed = discord.Embed(
            title=f"{char_name} {char_surname}".strip(),
            description="Добро пожаловать в мир! Используйте кнопки ниже для взаимодействия.",
            color=discord.Color.dark_gold()
        )
        # Сюда можно добавить поля с HP/MP, статусом и т.д.
        embed.add_field(name="Статус", value="В безопасности", inline=True)
        embed.add_field(name="Локация", value="Город", inline=True) # Это можно будет брать из данных локации

        embed.set_footer(text="Ваше приключение ждет.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """ Проверяет, что взаимодействие исходит от автора View. """
        if interaction.user.id == self.author.id:
            return True
        await interaction.response.send_message("Вы не можете использовать эту панель.", ephemeral=True)
        return False