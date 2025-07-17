

import discord
from typing import Optional, Dict, Any, List

from game_server.app_discord_bot.app.ui.components.buttons.universal_buttons import BackButton, ConfirmButton, ExitButton, ObserveButton
from game_server.app_discord_bot.app.ui.components.selects.map_location_select import MapLocationSelect

# Импортируем готовые компоненты


# --- Базовый класс для всех навигационных View ---

class BaseNavigationView(discord.ui.View):
    """
    Базовый класс для всех View, отображающих локации.
    Содержит общую логику создания эмбеда и проверки автора.
    """
    def __init__(self, author: discord.User, data: Dict[str, Any]):
        super().__init__(timeout=None)
        self.author = author
        self.location_data = data.get("location_info", {})
        self.transitions = data.get("transitions", [])
        
        # Переменные для хранения состояния
        self.selected_location_id: Optional[str] = None
        
        # Вызываем метод сборки UI, который будет переопределен в дочерних классах
        self.setup_ui()

    def setup_ui(self):
        """
        Абстрактный метод для сборки интерфейса.
        Дочерние классы должны реализовать его.
        """
        raise NotImplementedError("Дочерний класс должен реализовать метод setup_ui")

    def create_embed(self) -> discord.Embed:
        """Создает Embed с описанием текущей локации."""
        embed = discord.Embed(
            title=f"📍 {self.location_data.get('name', 'Неизвестная локация')}",
            description=self.location_data.get('description', 'Описание отсутствует...'),
            color=discord.Color.dark_teal()
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """ Проверяет, что взаимодействие исходит от автора View. """
        if interaction.user.id == self.author.id:
            return True
        await interaction.response.send_message("Это не ваша навигационная панель.", ephemeral=True)
        return False

    # --- Методы-обработчики для компонентов, которые могут быть вызваны из дочерних View ---

    async def on_location_select(self, interaction: discord.Interaction, location_id: str):
        """
        Вызывается из MapLocationSelect.callback.
        Устанавливает выбранный ID локации и активирует кнопку перехода,
        обновляя ее custom_id.
        """
        self.selected_location_id = location_id
        for item in self.children:
            # ИЗМЕНЕНО: Проверяем custom_id, начинающийся с "navigation:move_to" (вместо "navigation:go")
            if isinstance(item, ConfirmButton) and item.custom_id.startswith("navigation:move_to"): # <--- ИЗМЕНЕНО
                # ИЗМЕНЕНО: Обновляем custom_id, чтобы включить выбранный location_id с префиксом "navigation:move_to"
                item.custom_id = f"navigation:move_to:{self.selected_location_id}" # <--- ИЗМЕНЕНО
                item.disabled = False
                break
        await interaction.response.edit_message(view=self)

# --- Реализации для каждого типа локации ---

class ExternalLocationView(BaseNavigationView):
    """
    Стандартный вид навигации для большинства внешних локаций.
    Включает переходы, осмотр и кнопку "Назад".
    """
    def setup_ui(self):
        if self.transitions:
            select = MapLocationSelect(self.transitions)
            select.view_parent = self
            self.add_item(select)

            # Кнопка подтверждения с командой для сервиса 'navigation'
            # ИЗМЕНЕНО: custom_id теперь начинается с "navigation:move_to"
            self.add_item(ConfirmButton(label="Идти", custom_id="navigation:move_to", disabled=True))

        # 2. Кнопка "Осмотреться" с командой для сервиса 'inspection'
        self.add_item(ObserveButton(custom_id="inspection:look_around"))
        
        # 3. Кнопка "Назад" с командой для сервиса 'navigation'
        self.add_item(BackButton(custom_id="navigation:back"))


class HubLocationView(BaseNavigationView):
    """
    Вид для стартовой локации (Хаба).
    То же, что и External, но без кнопки "Назад".
    """
    def setup_ui(self):
        # 1. Список переходов и кнопка "Идти"
        if self.transitions:
            select = MapLocationSelect(self.transitions)
            select.view_parent = self # ЭТО СНОВА НУЖНО
            self.add_item(select)
            # ИЗМЕНЕНО: custom_id теперь начинается с "navigation:move_to"
            self.add_item(ConfirmButton(label="Идти", custom_id="navigation:move_to", disabled=True))

        # 2. Кнопка "Осмотреться"
        self.add_item(ObserveButton(custom_id="inspection:look_around"))


class InternalLocationView(BaseNavigationView):
    """
    Вид для "тупиковых" локаций (помещения, пещеры).
    Только "Осмотреться" и "Выйти".
    """
    def setup_ui(self):
        # 1. Кнопка "Осмотреться"
        self.add_item(ObserveButton(custom_id="inspection:look_around"))
        
        # 2. Кнопка "Выйти", которая использует ту же команду, что и "Назад"
        self.add_item(ExitButton(custom_id="navigation:back"))
