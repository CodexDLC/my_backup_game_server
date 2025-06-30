import discord
from typing import List, Dict, Any

class CharacterSelect(discord.ui.Select):
    """
    Специализированный выпадающий список для выбора игрового персонажа.
    Предполагается, что на вход всегда подается непустой список персонажей.
    """
    def __init__(self, characters: List[Dict[str, Any]]):
        """
        Инициализирует список выбора персонажей.

        Args:
            characters (List[Dict[str, Any]]): Список словарей, где каждый словарь 
                                              представляет одного персонажа.
                                              Ожидаемые ключи: 'id', 'name', 'level', 'class'.
        """
        
        options: List[discord.SelectOption] = []
        for char in characters:
            options.append(discord.SelectOption(
                label=char.get('name', 'Безымянный'),
                value=str(char.get('id', 'error_id')), # Value должен быть строкой
                description=f"{char.get('class', 'Класс не указан')}, {char.get('level', '?')} уровень",
                emoji="👤"
            ))

        super().__init__(
            placeholder="Выберите вашего персонажа для входа...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Вызывается, когда пользователь делает выбор.
        Делегирует обработку родительскому View, передавая ID персонажа.
        """
        if self.values: # self.values[0] будет содержать ID выбранного персонажа.
            if hasattr(self.view, 'on_character_select'):
                await self.view.on_character_select(interaction, self.values[0])