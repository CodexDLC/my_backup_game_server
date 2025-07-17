import discord

class TestTriggerView(discord.ui.View):
    """
    Шаблон View с одной кнопкой для запуска тестового цикла.
    """
    def __init__(self):
        # timeout=None делает кнопку постоянной
        super().__init__(timeout=None)
        
        # Создаем кнопку с нашим структурированным custom_id
        button = discord.ui.Button(
            label="Запустить тест",
            style=discord.ButtonStyle.primary,
            custom_id="test_example:get_data:start"
        )
        self.add_item(button)