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

                # =================================================================
                # ПРИМЕЧАНИЕ ДЛЯ РЕДАКТИРОВАНИЯ:
                # Ниже представлена ВРЕМЕННАЯ структура данных, которую мы ожидаем от бэкенда.
                # Когда вы определитесь с точной структурой в вашей базе данных,
                # нужно будет изменить код в цикле `for loc in locations:` ниже,
                # чтобы он соответствовал вашим новым названиям полей.
                # 
                # ПРИМЕР ВРЕМЕННОЙ СТРУКТУРЫ:
                # [
                #   {'id': 'loc_01', 'name': 'Таверна "Пьяный Гоблин"', 'travel_time': 5},
                #   {'id': 'loc_02', 'name': 'Рыночная площадь', 'travel_time': 10},
                # ]
                # =================================================================
        """
        
        options: List[discord.SelectOption] = []
        
        # --- НАЧАЛО БЛОКА ДЛЯ РЕДАКТИРОВАНИЯ ---
        # Этот цикл зависит от финальной структуры данных с бэкенда.
        for loc in locations:
            # Безопасно получаем данные с помощью .get(), чтобы избежать ошибок,
            # если ключ отсутствует.
            label_text = loc.get('name', 'Неизвестная локация')
            value_id = str(loc.get('id', 'error_id'))
            description_text = f"Время в пути: {loc.get('travel_time', '?')} мин."
            
            options.append(discord.SelectOption(
                label=label_text,
                value=value_id,
                description=description_text,
                emoji="📍"
            ))
        # --- КОНЕЦ БЛОКА ДЛЯ РЕДАКТИРОВАНИЯ ---

        super().__init__(
            placeholder="Выберите, куда отправиться...",
            min_values=1,
            max_values=1,
            options=options,
            disabled=(not locations) # Список будет неактивен, если локаций для перехода нет
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Вызывается, когда пользователь делает выбор.
        Делегирует обработку родительскому View.
        """
        if self.values:
            if hasattr(self.view, 'on_location_select'):
                await self.view.on_location_select(interaction, self.values[0])