import discord
from typing import Optional, Dict, Any, List

from Discord_API.core.ui.components.buttons import BackButton, CharactersButton, DeckButton, EnterWorldButton, LoginButton
from Discord_API.core.ui.components.selects.character_select import CharacterSelect

# Используем относительный импорт, чтобы достать компоненты из соседних папок

# В этом файле теперь будет полный набор View для всего процесса входа

class InitialLoginView(discord.ui.View):
    """Самый первый View, который видит игрок."""
    # ... (код этого класса остается без изменений, как в прошлый раз)
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(LoginButton())
    
    # ... (методы create_welcome_embed, interaction_check, on_login) ...
    # Метод on_login будет вызывать и показывать LobbyView, как мы и обсуждали.


class LobbyView(discord.ui.View):
    """
    View для экрана "Лобби". Появляется после нажатия "Войти в игру".
    """
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

        self.add_item(CharactersButton())
        self.add_item(DeckButton())

    def create_embed(self) -> discord.Embed:
        """Создает Embed для Лобби."""
        return discord.Embed(
            title="Лобби Аккаунта",
            description="Выберите, что вы хотите сделать.",
            color=discord.Color.blue()
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    async def on_characters(self, interaction: discord.Interaction):
        """Вызывается при нажатии на [Персонажи]. Должен показать CharacterLoginView."""
        # Здесь будет вызов функции из "слоя логики", которая:
        # 1. Запросит у бэкенда список персонажей
        # 2. Решит, какой View показать (CharacterLoginView или NoCharactersView)
        # 3. Отредактирует второе сообщение, добавив в него нужный View
        await interaction.response.send_message("Загрузка списка персонажей...", ephemeral=True)

    async def on_deck(self, interaction: discord.Interaction):
        """Вызывается при нажатии на [Колода]. Должен показать DeckView (заглушку)."""
        # Здесь будет вызов функции из "слоя логики", которая
        # отредактирует второе сообщение, показав в нем DeckView
        await interaction.response.send_message("Загрузка меню колоды...", ephemeral=True)

class DeckView(discord.ui.View):
    """View-заглушка для меню управления колодой."""
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(BackButton())
        
    def create_embed(self) -> discord.Embed:
        return discord.Embed(
            title="🃏 Управление колодой",
            description="Эта функция находится в разработке и появится в будущих обновлениях.",
            color=discord.Color.light_grey()
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    async def on_back(self, interaction: discord.Interaction):
        """Возвращает игрока в Лобби, очищая второе сообщение."""
        # Логика, которая редактирует второе сообщение, возвращая его в исходное состояние
        await interaction.response.edit_message(content="...", embed=None, view=None)


class CharacterLoginView(discord.ui.View):
    """View для выбора персонажа и входа в мир."""
    def __init__(self, author: discord.User, characters: List[Dict[str, Any]]):
        super().__init__(timeout=None)
        self.author = author
        self.selected_character_id: Optional[str] = None
        
        # Создаем и добавляем компоненты
        self.select_menu = CharacterSelect(characters)
        self.confirm_button = EnterWorldButton()
        self.confirm_button.disabled = True # Кнопка неактивна, пока не выбран персонаж
        
        self.add_item(self.select_menu)
        self.add_item(self.confirm_button)
        self.add_item(BackButton())

    def create_embed(self) -> discord.Embed:
        return discord.Embed(
            title="Выбор персонажа",
            description="Выберите одного из ваших героев, чтобы войти в мир.",
            color=discord.Color.green()
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    async def on_character_select(self, interaction: discord.Interaction, character_id: str):
        """Вызывается из CharacterSelect. Сохраняет выбор и активирует кнопку."""
        self.selected_character_id = character_id
        self.confirm_button.disabled = False # Активируем кнопку
        
        # Обновляем сообщение, чтобы показать активную кнопку
        await interaction.response.edit_message(view=self)

    async def on_enter_world(self, interaction: discord.Interaction):
        """Вызывается при нажатии [Войти в мир]. Финальный шаг."""
        # Здесь логика вызывает бэкенд с self.selected_character_id,
        # а затем заменяет ОБА сообщения на основной игровой интерфейс.
        await interaction.response.edit_message(content=f"Вход в мир за персонажа с ID: {self.selected_character_id}...", view=None, embed=None)

    async def on_back(self, interaction: discord.Interaction):
        """Возвращает игрока в Лобби, очищая второе сообщение."""
        # Логика, которая редактирует второе сообщение, возвращая его в исходное состояние
        await interaction.response.edit_message(content="...", embed=None, view=None)