# game_server/app_discord_bot/app/ui/views/authentication/character_selection_view.py

import discord
from typing import Optional, List
import inject 
import logging 

# Импортируем наши новые универсальные кнопки
from game_server.app_discord_bot.app.ui.components.buttons.authentication_buttons import EnterWorldButton, StartAdventureButton
from game_server.app_discord_bot.app.ui.components.buttons.universal_buttons import BackButton
from game_server.app_discord_bot.app.ui.components.selects.character_select import CharacterSelect
from game_server.contracts.dtos.character.data_models import CharacterDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager


# --- Базовый класс для общих проверок View ---
class BaseAuthView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Проверяет, что взаимодействие исходит от автора View."""
        if interaction.user.id == self.author.id:
            return True
        await interaction.response.send_message("Вы не можете использовать это меню.", ephemeral=True)
        return False

# --- Класс 1: CharacterSelectionView (когда есть персонажи) ---
class CharacterSelectionView(BaseAuthView):
    """
    View для выбора персонажа. Кнопки теперь генерируют команды.
    """
    @inject.autoparams()
    def __init__(self, author: discord.User, characters: List[CharacterDTO], account_data_manager: IAccountDataManager, logger: logging.Logger):
        super().__init__(author=author)
        self.selected_character_id: Optional[int] = None
        self.account_data_manager = account_data_manager
        self.characters = characters 
        self.logger = logger
        
        # 1. Выпадающий список
        self.select_menu = CharacterSelect(characters)
        self.select_menu.callback = self.on_character_select_callback
        self.add_item(self.select_menu)
        
        # 2. Кнопка "Войти в мир"
        self.enter_world_button = EnterWorldButton(
            custom_id="lobby:enter_world", 
            disabled=True
        )
        self.add_item(self.enter_world_button)

        # 3. Кнопка "Назад"
        self.add_item(BackButton(custom_id="lobby:back_to_main"))

    def create_embed(self) -> discord.Embed:
        description_lines = ["Выберите одного из ваших героев, чтобы войти в мир:\n"]
        if self.characters:
            for char in self.characters:
                char_name = getattr(char, 'name', 'Безымянный')
                char_id = getattr(char, 'character_id', 'N/A')
                char_status = getattr(char, 'status', 'Неизвестно')
                description_lines.append(f"• **{char_name}** (ID: {char_id}) - Статус: {char_status}")
        else:
            description_lines.append("У вас пока нет персонажей.")

        return discord.Embed(
            title="Выберите персонажа",
            description="\n".join(description_lines),
            color=discord.Color.green()
        )
    
    async def on_character_select_callback(self, interaction: discord.Interaction):
        self.logger.debug(f"DEBUG: on_character_select_callback вызван для пользователя {interaction.user.name}.")
        self.logger.debug(f"DEBUG: interaction.data: {interaction.data}")

        # НОВОЕ: Откладываем ответ, чтобы у Discord было время на обработку
        await interaction.response.defer() 

        selected_value = interaction.data.get('values', [None])[0]
        
        if selected_value:
            self.logger.debug(f"DEBUG: Выбрано значение: {selected_value}")
            try:
                self.selected_character_id = int(selected_value)
                self.logger.debug(f"DEBUG: selected_character_id установлен в {self.selected_character_id}.")
                self.enter_world_button.disabled = False
                self.logger.debug("DEBUG: Кнопка 'Войти в мир' активирована.")
                
                # Обновляем custom_id кнопки "Войти в мир" с ID выбранного персонажа
                self.enter_world_button.custom_id = f"lobby:enter_world:{self.selected_character_id}"
                self.logger.debug(f"DEBUG: custom_id кнопки 'Войти в мир' обновлен на {self.enter_world_button.custom_id}.")

                # Обновляем placeholder, чтобы пользователь видел свой выбор
                selected_option_label = next((opt.label for opt in self.select_menu.options if opt.value == selected_value), "Неизвестно")
                self.select_menu.placeholder = f"Выбран: {selected_option_label}"
                self.logger.debug(f"DEBUG: Placeholder выпадающего списка обновлен на '{self.select_menu.placeholder}'.")
                
                # НОВОЕ: Используем edit_original_response после defer
                await interaction.edit_original_response(view=self)
                self.logger.debug("DEBUG: Сообщение Discord отредактировано с обновленным View.")
            except Exception as e:
                self.logger.error(f"ОШИБКА в on_character_select_callback: {e}", exc_info=True)
                # Если defer уже был, используем followup
                await interaction.followup.send("Произошла ошибка при выборе персонажа. Пожалуйста, попробуйте снова.", ephemeral=True)
        else:
            self.logger.debug("DEBUG: selected_value пуст или не найден.")
            # Если defer уже был, используем followup
            await interaction.followup.send("Пожалуйста, выберите персонажа.", ephemeral=True)


# --- Класс 2: NoCharactersView (когда нет персонажей) ---
class NoCharactersView(BaseAuthView):
    """
    View, когда у игрока нет персонажей. Кнопки генерируют команды.
    """
    def __init__(self, author: discord.User):
        super().__init__(author=author)
        
        self.add_item(StartAdventureButton(custom_id="lobby:start_adventure"))
        
        self.add_item(BackButton(custom_id="lobby:back_to_main"))

    def create_embed(self) -> discord.Embed:
        return discord.Embed(
            title="Начните приключение!",
            description="Кажется, у вас еще нет персонажей. Нажмите 'Начать приключение', чтобы получить первого случайного героя и отправиться в игру!",
            color=discord.Color.blue()
        )
