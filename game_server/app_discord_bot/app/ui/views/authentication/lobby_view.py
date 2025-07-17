import discord
import inject

# Импортируем тексты
from game_server.app_discord_bot.app.ui.components.buttons.authentication_buttons import CharactersButton, DeckButton, LogoutButton
from game_server.app_discord_bot.app.ui.messages.authentication import lobby_messages
# Импортируем классы кнопок


class LobbyView(discord.ui.View):
    """
    View для "Панели Интерфейса Лобби".
    Теперь кнопки генерируют команды, а не вызывают коллбэки.
    """
    @inject.autoparams()
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

        # 🔥 ИЗМЕНЕНИЕ: Кнопка "Персонажи" теперь использует custom_id
        characters_button = CharactersButton(custom_id="lobby:show_characters", row=0)
        self.add_item(characters_button)

        # 🔥 ИЗМЕНЕНИЕ: Кнопка "Колода" теперь использует custom_id
        deck_button = DeckButton(custom_id="lobby:show_deck", row=0)
        self.add_item(deck_button)
        
        # 🔥 НОВОЕ: Добавляем кнопку "Разлогиниться"
        logout_button = LogoutButton(custom_id="lobby:logout", row=1)
        self.add_item(logout_button)
    
    def create_embed(self) -> discord.Embed:
        """Создает основной Embed для лобби."""
        embed = discord.Embed(
            title=lobby_messages.LOBBY_TOP_EMBED_TITLE,
            description=lobby_messages.LOBBY_TOP_EMBED_DESCRIPTION,
            color=discord.Color.blue()
        )
        embed.set_footer(text=lobby_messages.LOBBY_TOP_EMBED_FOOTER)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Проверяет, что с View взаимодействует его владелец."""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Вы не можете использовать это меню.", ephemeral=True)
            return False
        return True
    
    # Старые коллбэки on_characters и on_deck можно удалить.
