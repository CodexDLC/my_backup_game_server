import discord
from typing import List, Dict, Any

class MapLocationSelect(discord.ui.Select):
    """
    Специализированный выпадающий список для выбора локации на карте.
    """
    def __init__(self, locations: List[Dict[str, Any]]):
        """
        Инициализирует список выбора локаций.

        Args:
            locations (List[Dict[str, Any]]):
                Список словарей, где каждый словарь представляет одну локацию.
        """
        
        options: List[discord.SelectOption] = []
        
        # Этот цикл зависит от финальной структуры данных с бэкенда.
        for loc in locations:
            # Используем 'label' вместо 'name'
            label_text = loc.get('label', 'Неизвестный переход')
            
            # Используем 'target_location_id' вместо 'id'
            value_id = str(loc.get('target_location_id', 'error_id'))
            
            options.append(discord.SelectOption(
                label=label_text,
                value=value_id,
                description=None, # Описание убрано, так как данных о времени пути нет
                emoji="📍"
            ))

        super().__init__(
            placeholder="Выберите, куда отправиться...",
            min_values=1,
            max_values=1,
            options=options,
            disabled=(not locations) # Список будет неактивен, если локаций для перехода нет
            # custom_id больше не нужен здесь, так как есть callback
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Вызывается, когда пользователь делает выбор.
        Делегирует обработку родительскому View.
        """
        if self.values:
            if hasattr(self.view, 'on_location_select'):
                await self.view.on_location_select(interaction, self.values[0])

