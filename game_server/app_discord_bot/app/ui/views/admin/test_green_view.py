import discord

class TestGreenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Эта кнопка отправит команду на переключение в состояние "B" (красное)
        button = discord.ui.Button(
            label="Нажми для теста (Зеленая)",
            style=discord.ButtonStyle.success, # Зеленая кнопка
            custom_id="test_example:toggle_state:B"
        )
        self.add_item(button)