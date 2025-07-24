# game_server/app_discord_bot/app/ui/views/inspection/inspection_list_views.py

import discord
from typing import Optional, List, Dict, Any

# Импортируем универсальные кнопки
from ....ui.components.buttons.universal_buttons import BackButton
# Импортируем наши DTO из модуля inspection
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import InspectionListDTO
# Импортируем базовый View для осмотра
from .overview_views import BaseInspectionView
# Импортируем компоненты Select и кнопку ViewDetailsActionButton для 2-го уровня
from .components import EntitySelect, ViewDetailsActionButton


class BaseCategoryListView(BaseInspectionView):
    """
    Базовый класс для отображения списков объектов в выбранной категории.
    Содержит общую логику для пагинации, кнопки "Назад" и управления EntitySelect.
    На 2-м уровне всегда добавляет только кнопку "Взаимодействовать".
    """
    def __init__(self, author: discord.User, dto: InspectionListDTO):
        super().__init__(author)
        self.dto = dto  # Сохраняем DTO для доступа в коллбэках
        self.selected_entity_id: Optional[str] = None # ID выбранной сущности
        self.action_buttons_map: Dict[str, discord.ui.Button] = {} # Словарь для доступа к кнопкам по их ключу

        # Добавляем выпадающий список
        if dto.entities:
            select_component = EntitySelect(dto.entities, dto.pagination.category_key if dto.pagination else "unknown_category")
            self.add_item(select_component) # discord.py сам установит .view после add_item

        # Добавляем кнопки пагинации, если есть несколько страниц
        if dto.pagination and dto.pagination.total_pages > 1:
            p = dto.pagination
            prev_page_button = discord.ui.Button(
                label="<",
                style=discord.ButtonStyle.primary,
                custom_id=f"inspection:list_category:{p.category_key}:page:{p.current_page - 1}",
                disabled=(p.current_page <= 1)
            )
            next_page_button = discord.ui.Button(
                label=">",
                style=discord.ButtonStyle.primary,
                custom_id=f"inspection:list_category:{p.category_key}:page:{p.current_page + 1}",
                disabled=(p.current_page >= p.total_pages)
            )
            self.add_item(prev_page_button)
            self.add_item(next_page_button)

        # Кнопка "Назад" для возврата на экран общего обзора (первый уровень)
        self.add_item(BackButton(custom_id="inspection:look_around"))

        # Вызываем метод для добавления специфических кнопок действий
        self._add_category_specific_buttons()

        # Изначально все добавленные кнопки действий должны быть неактивны
        self.disable_all_action_buttons()


    def _add_category_specific_buttons(self):
        """
        Метод для добавления специфических кнопок действий.
        На 2-м уровне это всегда только кнопка "Взаимодействовать".
        """
        self.view_details_button = ViewDetailsActionButton(custom_id="inspection:action:view_details:TEMP_ID")
        self.add_item(self.view_details_button)
        self.action_buttons_map["view_details"] = self.view_details_button # Сохраняем ссылку


    def disable_all_action_buttons(self):
        """Деактивирует все кнопки действий, добавленные в этот View."""
        for button in self.action_buttons_map.values():
            button.disabled = True

    async def on_entity_selected(self, interaction: discord.Interaction, selected_entity_id: str, category_key: str):
        """
        Вызывается из EntitySelect.callback после выбора сущности.
        Активирует кнопку "Взаимодействовать" и обновляет ее custom_id.
        """
        self.selected_entity_id = selected_entity_id  # Сохраняем выбранный ID

        # Деактивируем все кнопки сначала
        self.disable_all_action_buttons()

        # Активируем только кнопку "Взаимодействовать"
        if "view_details" in self.action_buttons_map:
            button = self.action_buttons_map["view_details"]
            button.disabled = False
            # Обновляем custom_id кнопки, добавляя ID выбранной сущности
            button.custom_id = f"inspection:action:view_details:{selected_entity_id}"
        
        # Отправляем отредактированное сообщение с активированными кнопками
        await interaction.response.edit_message(view=self)


# --- Специализированные View для каждой категории (УДАЛЕНЫ, так как не имеют уникальной логики на 2-м уровне) ---
# Теперь DisplayInspectionListPresenter будет всегда использовать BaseCategoryListView.

