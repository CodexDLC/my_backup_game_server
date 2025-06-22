import discord
from typing import Optional, Dict, Any, List

from Discord_API.core.ui.components.buttons import ConfirmButton, ObserveButton
from Discord_API.core.ui.components.selects.map_location_select import MapLocationSelect

# Импортируем наши готовые компоненты


class LocationView(discord.ui.View):
    """
    Универсальный "скелет" для отображения любой игровой локации.
    Динамически собирает свой интерфейс на основе данных, полученных от бэкенда.
    """
    def __init__(self, author: discord.User, data: Dict[str, Any]):
        super().__init__(timeout=None)
        self.author = author
        self.data = data
        
        # Переменные для хранения состояния
        self.selected_location_id: Optional[str] = None
        self.selected_event_id: Optional[str] = None

        # Собираем интерфейс на основе полученных данных
        self.setup_ui()

    def setup_ui(self):
        """Динамически собирает интерфейс на основе self.data."""
        
        # 1. Добавляем список переходов, если они есть
        transitions = self.data.get('transitions', [])
        if transitions:
            self.add_item(MapLocationSelect(transitions))
            
            # Кнопка для подтверждения перехода
            self.confirm_move_button = ConfirmButton(label="Идти")
            self.confirm_move_button.disabled = True # Изначально неактивна
            self.add_item(self.confirm_move_button)

        # 2. Добавляем постоянную кнопку "Осмотреться"
        self.add_item(ObserveButton())
        
        # 3. Динамически добавляем кнопки для глобальных событий
        #    (согласно нашему последнему обсуждению)
        events = self.data.get('events', [])
        if events:
            for event in events:
                # Создаем кнопку для события "на лету"
                event_button = discord.ui.Button(
                    label=event.get('name', 'Событие'),
                    style=discord.ButtonStyle.primary,
                    custom_id=f"event_{event.get('event_id', 'unknown')}"
                )
                
                async def event_callback(interaction: discord.Interaction):
                    # Эта вложенная функция будет вызывать обработчик событий в слое логики
                    # self.logic_handler.handle_event(interaction, interaction.data['custom_id'])
                    await interaction.response.send_message(f"Вы выбрали событие: {interaction.data['custom_id']}", ephemeral=True)
                
                event_button.callback = event_callback
                self.add_item(event_button)

    def create_embed(self) -> discord.Embed:
        """Создает Embed с описанием текущей локации."""
        location_info = self.data.get('location_info', {})
        embed = discord.Embed(
            title=location_info.get('name', 'Неизвестная локация'),
            description=location_info.get('description', '...'),
            color=discord.Color.dark_green()
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    # --- Методы-обработчики для наших компонентов ---

    async def on_location_select(self, interaction: discord.Interaction, location_id: str):
        """Вызывается из MapLocationSelect. Активирует кнопку перехода."""
        self.selected_location_id = location_id
        self.confirm_move_button.disabled = False
        await interaction.response.edit_message(view=self)

    async def on_confirm(self, interaction: discord.Interaction):
        """Вызывается из ConfirmButton. Запускает перемещение."""
        # Здесь будет вызов слоя логики для перемещения персонажа
        # self.logic_handler.move_player_to(self.selected_location_id)
        await interaction.response.edit_message(content=f"Переход в локацию {self.selected_location_id}...", view=None, embed=None)

    async def on_observe(self, interaction: discord.Interaction):
        """Вызывается из ObserveButton. Запускает "осмотр"."""
        # Здесь будет вызов слоя логики, который:
        # 1. Запросит у бэкенда локальные события
        # 2. Создаст новый ObservationView
        # 3. Отредактирует это сообщение, заменив LocationView на ObservationView
        await interaction.response.send_message("Вы осматриваетесь...", ephemeral=True)