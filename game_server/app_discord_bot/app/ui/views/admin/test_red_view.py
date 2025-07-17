import discord

class TestRedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Эта кнопка отправит команду на переключение в состояние "A" (зеленое)
        button = discord.ui.Button(
            label="Нажми для теста (Красная)",
            style=discord.ButtonStyle.danger, # Красная кнопка
            custom_id="test_example:toggle_state:A"
        )
        self.add_item(button)