# game_server/app_discord_bot/app/ui/components/selects/character_select.py

import discord
from discord.ui import Select
from discord.ext import commands
from typing import List, Optional

from game_server.contracts.dtos.character.data_models import CharacterDTO # Убедитесь, что CharacterDTO импортирован

class CharacterSelect(Select):
    def __init__(self, characters: List[CharacterDTO]):
        super().__init__(
            placeholder="Выберите персонажа для входа в мир...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    # Отображаем только имя персонажа
                    label=getattr(char, 'name', 'Безымянный'),
                    # ИЗМЕНЕНО: Удалено поле description
                    value=str(char.character_id) # ID персонажа как строка для value (скрытое значение)
                )
                for char in characters
            ]
        )
        self.characters = characters # Сохраняем список персонажей
