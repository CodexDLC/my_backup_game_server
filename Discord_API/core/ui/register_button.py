import discord

class RegistrationView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="Войти", style=discord.ButtonStyle.green)
    async def enter_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Привязываем кнопку к команде `enter_game()` в `RegistrationCog`"""
        command = interaction.client.get_command("enter_game")  # 🔥 Берём команду из `Cog`
        if command:
            await interaction.client.invoke(command.callback, interaction)  # ✅ Запускаем команду
        else:
            await interaction.response.send_message("Ошибка! Команда 'Войти' не найдена.", ephemeral=True)

    @discord.ui.button(label="Регистрация", style=discord.ButtonStyle.blurple)
    async def register_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Привязываем кнопку к команде `register_user()` в `RegistrationCog`"""
        command = interaction.client.get_command("register_user")  # 🔥 Берём команду из `Cog`
        if command:
            await interaction.client.invoke(command.callback, interaction)  # ✅ Запускаем команду
        else:
            await interaction.response.send_message("Ошибка! Команда 'Регистрация' не найдена.", ephemeral=True)
