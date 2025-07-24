# game_server/app_discord_bot/app/ui/views/inspection/overview_views.py

import discord
from typing import Optional, List

# Импортируем универсальные кнопки
from ....ui.components.buttons.universal_buttons import BackButton
# Импортируем наши DTO из модуля inspection
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import LookAroundResultObjectDTO, InspectionCategoryDTO

class BaseInspectionView(discord.ui.View):
    """Базовый класс для View в модуле осмотра."""
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author.id:
            return True
        await interaction.response.send_message("Это не ваша панель осмотра.", ephemeral=True)
        return False

# --- Экран 1: Выбор категории (ОБНОВЛЕНО для LookAroundResultObjectDTO) ---

class OverviewCategoriesView(BaseInspectionView):
    """
    Отображает кнопки для выбора категории объектов на экране общего обзора.
    Использует LookAroundResultObjectDTO для создания кнопок.
    """
    def __init__(self, author: discord.User, categories_data: List[LookAroundResultObjectDTO]):
        super().__init__(author)
        
        # Создаем кнопки для каждой категории
        for category in categories_data:
            # Используем display_name из LookAroundResultObjectDTO
            button_label = category.display_name
            # custom_id для перехода к списку категории (второй уровень)
            custom_id = f"inspection:list_category:{category.category_key}"
            self.add_item(discord.ui.Button(label=button_label, custom_id=custom_id, style=discord.ButtonStyle.secondary))
            
        # Кнопка "Назад" для возврата в навигацию (как указано в ТЗ для первого уровня)
        self.add_item(BackButton(custom_id="navigation:show_navigation"))