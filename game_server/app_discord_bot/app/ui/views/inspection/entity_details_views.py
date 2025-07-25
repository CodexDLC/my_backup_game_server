# game_server/app_discord_bot/app/ui/views/inspection/entity_details_views.py

import discord
from typing import Dict, Type

# Убедитесь, что импорты корректны для вашей структуры
from game_server.app_discord_bot.app.ui.style_mapping.ui_style_mapping import get_discord_button_style
from .overview_views import BaseInspectionView
from ....services.game_modules.inspection.inspection_dtos import EntityDetailsDTO
from ....ui.components.buttons.universal_buttons import BackButton

class BaseEntityDetailsView(BaseInspectionView):
    """
    Базовый View для отображения детальной информации о сущности (3-й уровень).
    """
    def __init__(self, author: discord.User, dto: EntityDetailsDTO):
        super().__init__(author)
        self.dto = dto
        self.action_buttons_map: Dict[str, discord.ui.Button] = {}

        self.add_item(BackButton(custom_id=f"inspection:list_category:{self.dto.category_key}", row=0))
        self._add_specific_fixed_buttons()
        self._add_dynamic_action_buttons()

    def _add_specific_fixed_buttons(self):
        """Метод для добавления специфических, фиксированных кнопок."""
        pass

    def _add_dynamic_action_buttons(self):
        """Добавляет динамические кнопки действий, полученные из DTO."""
        for action_dto in self.dto.actions:
            # Логика создания custom_id с использованием шаблона
            if action_dto.custom_id_template:
                custom_id = action_dto.custom_id_template.format(entity_id=self.dto.entity_id)
            else:
                # Запасной вариант, если шаблон не предоставлен
                custom_id = f"inspection:action:{action_dto.key}:{self.dto.entity_id}"
            
            button = discord.ui.Button(
                custom_id=custom_id,
                label=action_dto.label,
                style=get_discord_button_style(action_dto.style),
                disabled=action_dto.disabled,
                row=1 # Все динамические кнопки будут во втором ряду
            )
            self.add_item(button)
            self.action_buttons_map[action_dto.key] = button

# --- Специализированные View для 3-го уровня ---

class PlayerDetailsView(BaseEntityDetailsView):
    """View для отображения деталей игрока."""
    def _add_specific_fixed_buttons(self):
        # Кнопка "Торговать"
        self.trade_button = discord.ui.Button(label="Торговать", style=discord.ButtonStyle.green, custom_id=f"trade:initiate:{self.dto.entity_id}", row=0)
        self.add_item(self.trade_button)

        # Кнопка "Пригласить в пати"
        self.invite_party_button = discord.ui.Button(label="Пригласить в пати", style=discord.ButtonStyle.primary, custom_id=f"party:invite:{self.dto.entity_id}", row=0)
        self.add_item(self.invite_party_button)
        
class NpcDetailsView(BaseEntityDetailsView):
    """View для отображения деталей НЕЙТРАЛЬНОГО NPC."""
    def _add_specific_fixed_buttons(self):
        # Для всех нейтральных NPC будет базовая кнопка "Поговорить"
        self.talk_button = discord.ui.Button(label="Поговорить", style=discord.ButtonStyle.primary, custom_id=f"interact:talk:{self.dto.entity_id}", row=0)
        self.add_item(self.talk_button)

class MonsterDetailsView(BaseEntityDetailsView):
    """View для отображения деталей ВРАЖДЕБНОГО NPC."""
    def _add_specific_fixed_buttons(self):
        # Для всех враждебных NPC будет базовая кнопка "Атаковать"
        self.attack_button = discord.ui.Button(label="Атаковать", style=discord.ButtonStyle.danger, custom_id=f"combat:attack:{self.dto.entity_id}", row=0)
        self.add_item(self.attack_button)